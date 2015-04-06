module UFuzz
module Net
  
  class Socket

    extend Forwardable

    attr_accessor :config
    attr_reader :remote_ip

    def_delegators(:@socket, :readline, :readline)

    def initialize(config)
      @config = config
      @read_buffer = ''
      @eof = false

      @config.family ||= ::Socket::Constants::AF_UNSPEC
      if @config.proxy_host
        @config.proxy_family  ||= ::Socket::Constants::AF_UNSPEC
      end

      connect
    end

    def read(max_length=nil)
      if @eof
        return nil
      elsif @config.nonblock
        begin
          if max_length
            until @read_buffer.length >= max_length
              @read_buffer << @socket.read_nonblock(max_length - @read_buffer.length)
            end
          else
            while true
              @read_buffer << @socket.read_nonblock(@config.chunk_size)
            end
          end
        rescue OpenSSL::SSL::SSLError => error
          if error.message == 'read would block'
            if IO.select([@socket], nil, nil, @config.read_timeout)
              retry
            else
              raise(UFuzz::Errors::Timeout.new("read timeout reached"))
            end
          else
            raise(error)
          end
        rescue Errno::EAGAIN, Errno::EWOULDBLOCK, IO::WaitReadable
          if IO.select([@socket], nil, nil, @config.read_timeout)
            retry
          else
            raise(UFuzz::Errors::Timeout.new("read timeout reached"))
          end
        rescue EOFError
          @eof = true
        end
        if max_length
          @read_buffer.slice!(0, max_length)
        else
          # read until EOFError, so return everything
          @read_buffer.slice!(0, @read_buffer.length)
        end
      else
        begin
          Timeout.timeout(@config.read_timeout) do
            @socket.read(max_length)
          end
        rescue Timeout::Error
          raise UFuzz::Errors::Timeout.new('read timeout reached')
        end
      end
    end

    def write(data)
      if @config.nonblock
        # We normally return from the return in the else block below, but
        # we guard that data is still something in case we get weird
        # values and String#[] returns nil. (This behavior has been observed
        # in the wild, so this is a simple defensive mechanism)
        while data
          begin
            # I wish that this API accepted a start position, then we wouldn't
            # have to slice data when there is a short write.
            written = @socket.write_nonblock(data)
          rescue OpenSSL::SSL::SSLError => error
            if error.message == 'write would block'
              if IO.select(nil, [@socket], nil, @config.write_timeout)
                retry
              else
                raise(UFuzz::Errors::Timeout.new("write timeout reached"))
              end
            else
              raise(error)
            end
          rescue Errno::EAGAIN, Errno::EWOULDBLOCK, IO::WaitWritable
            if IO.select(nil, [@socket], nil, @config.write_timeout)
              retry
            else
              raise(UFuzz::Errors::Timeout.new("write timeout reached"))
            end
          else
            # Fast, common case.
            # The >= seems weird, why would it have written MORE than we
            # requested. But we're getting some weird behavior when @socket
            # is an OpenSSL socket, where it seems like it's saying it wrote
            # more (perhaps due to SSL packet overhead?).
            #
            # Pretty weird, but this is a simple defensive mechanism.
            return if written >= data.size

            # This takes advantage of the fact that most ruby implementations
            # have Copy-On-Write strings. Thusly why requesting a subrange
            # of data, we actually don't copy data because the new string
            # simply references a subrange of the original.
            data = data[written, data.size]
          end
        end
      else
        begin
          Timeout.timeout(@config.write_timeout) do
            @socket.write(data)
          end
        rescue Timeout::Error
          UFuzz::Errors::Timeout.new('write timeout reached')
        end
      end
    end
    
    def close
      @socket.close unless @socket.closed?
    rescue => e
      puts e.message
      puts e.backtrace
    end
    
    private

    def connect
      @socket = nil
      exception = nil

      addrinfo = if @config.proxy_host
        ::Socket.getaddrinfo(@config.proxy_host, @config.proxy_port, @config.proxy_family, ::Socket::Constants::SOCK_STREAM)
      else
        ::Socket.getaddrinfo(@config.host, @config.port, @config.family, ::Socket::Constants::SOCK_STREAM)
      end

      addrinfo.each do |_, port, _, ip, a_family, s_type|
        @remote_ip = ip

        # nonblocking connect
        begin
          sockaddr = ::Socket.sockaddr_in(port, ip)

          socket = ::Socket.new(a_family, s_type, 0)

          if @config.nonblock
            socket.connect_nonblock(sockaddr)
          else
            begin
              Timeout.timeout(@config.connect_timeout) do
                socket.connect(sockaddr)
              end
            rescue Timeout::Error
              raise UFuzz::Errors::Timeout.new('connect timeout reached')
            end
          end

          @socket = socket
          break
        rescue Errno::EINPROGRESS
          unless IO.select(nil, [socket], nil, @config.connect_timeout)
            raise(UFuzz::Errors::Timeout.new("connect timeout reached"))
          end
          begin
            socket.connect_nonblock(sockaddr)

            @socket = socket
            break
          rescue Errno::EISCONN
            @socket = socket
            break
          rescue SystemCallError => exception
            socket.close
            next
          end
        rescue SystemCallError => exception
          socket.close if socket
          next
        end
      end

      unless @socket
        # this will be our last encountered exception
        raise exception
      end

      if @config.tcp_nodelay
        @socket.setsockopt(::Socket::IPPROTO_TCP,
                           ::Socket::TCP_NODELAY,
                           true)
      end
    end
  end

end
end