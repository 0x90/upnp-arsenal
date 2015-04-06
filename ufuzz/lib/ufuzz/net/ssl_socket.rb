module UFuzz
module Net
  
  class SSLSocket < Socket

    def initialize(config = {})
      @config = config
      check_nonblock_support

      super

      # create ssl context
      if config.ssl_version
        ssl_context = OpenSSL::SSL::SSLContext.new(config.ssl_version)
      else
        ssl_context = OpenSSL::SSL::SSLContext.new
      end

      if @config.ssl_verify_peer
        # turn verification on
        ssl_context.verify_mode = OpenSSL::SSL::VERIFY_PEER

        if ca_path = ENV['SSL_CERT_DIR'] || @config.ssl_ca_path
          ssl_context.ca_path = ca_path
        elsif ca_file = ENV['SSL_CERT_FILE'] || @config.ssl_ca_file
          ssl_context.ca_file = ca_file
        else # attempt default, fallback to bundled
          ssl_context.cert_store = OpenSSL::X509::Store.new
          ssl_context.cert_store.set_default_paths
          ssl_context.cert_store.add_file(DEFAULT_CA_FILE)
        end
      else
        # turn verification off
        ssl_context.verify_mode = OpenSSL::SSL::VERIFY_NONE
      end

      # maintain existing API
      certificate_path = @config.client_cert || @config.certificate_path
      private_key_path = @config.client_key  || @config.private_key_path

      if certificate_path && private_key_path
        ssl_context.cert = OpenSSL::X509::Certificate.new(File.read(certificate_path))
        ssl_context.key = OpenSSL::PKey::RSA.new(File.read(private_key_path))
      elsif @config.certificate && @config.private_key
        ssl_context.cert = OpenSSL::X509::Certificate.new(@config.certificate)
        ssl_context.key = OpenSSL::PKey::RSA.new(@config.private_key)
      end

      if @config.proxy_host
        request = 'CONNECT ' << @config.host << ':' << @config.port << UFuzz::HTTP_1_1
        request << 'Host: ' << @config.host << ':' << @config.port << UFuzz::CR_NL

        if @config.proxy_password || @config.proxy_user
          auth = ['' << @config.proxy_user.to_s << ':' << @config.proxy_password.to_s].pack('m').delete(UFuzz::CR_NL)
          request << "Proxy-Authorization: Basic " << auth << UFuzz::CR_NL
        end

        request << 'Proxy-Connection: Keep-Alive' << UFuzz::CR_NL

        request << UFuzz::CR_NL

        # write out the proxy setup request
        @socket.write(request)

        # eat the proxy's connection response
        UFuzz::Http::Response.parse(@socket, request)
      end

      # convert Socket to OpenSSL::SSL::SSLSocket
      @socket = OpenSSL::SSL::SSLSocket.new(@socket, ssl_context)
      @socket.sync_close = true
      @socket.connect

      # Server Name Indication (SNI) RFC 3546
      if @socket.respond_to?(:hostname=)
        @socket.hostname = @config.host
      end

      # verify connection
      if @config.ssl_verify_peer
        @socket.post_connection_check(@config.host)
      end

      @socket
    end

    def read(max_length=nil)
      check_nonblock_support
      super
    end

    def write(data)
      check_nonblock_support
      super
    end

    private

    def check_nonblock_support
      # backwards compatability for things lacking nonblock
      if !UFuzz::DEFAULT_NONBLOCK && @config.nonblock
        log "socket nonblock is not supported by your OpenSSL::SSL::SSLSocket", WARN
        @config.nonblock = false
      elsif UFuzz::DEFAULT_NONBLOCK
        @config.nonblock = true
      end
    end

    def connect
      check_nonblock_support
      super
    end

  end

end
end