module UFuzz
module Http

class Response
  attr_accessor :headers, :body, :status, :remote_ip, :data
  
  def initialize(resp)
    @headers  = resp[:headers]
    @body     = resp[:body]
    @status   = resp[:status]
    @remote_ip = resp[:remote_ip]
    @data     = nil
  end
  
  def to_s
    return @data if @data
    
    @data  = "HTTP/1.1 #{@status} #{UFuzz::HTTP_ERRORS[@status]}" + UFuzz::CR_NL # FIXME
    @data += @headers.each_pair.map do |k,v|
      "#{k}: #{v}"
    end.join(UFuzz::CR_NL)
    @data += UFuzz::CR_NL * 2
    @data += @body
  end
  
  def inspect
    "<#{"%x" % self.object_id} #{self.class}> @status => #{@status} " +
        "@headers => #{@headers.inspect} @body => #{@body.inspect}"
  end
  
  def first_line
    "HTTP/1.1 #{@status} #{UFuzz::HTTP_ERRORS[@status]}"
  end
  
  def summary
    "#{first_line} #{@body.length} bytes"
  end
  
  def code
    @status
  end
  
  def contains(*arr)
    arr.each do |m|
      if @body && @body =~ m
        return $0
      end
    end
    false
  end
  
  def self.parse(socket, req)
    config = UFuzz::Config.instance
    resp = {
      :body       => '',
      :headers    => {},
      :status     => -1,
      :remote_ip  => socket.respond_to?(:remote_ip) && socket.remote_ip
    }
    
    begin
      status_line = socket.read(12)
      raise SocketError, "no data" unless status_line
      
      resp[:status] = status_line[9, 11].to_i
      socket.readline # read the rest of the status line and CRLF

      until ((data = socket.readline).chop!).empty?
        key, value = data.split(/:\s*/, 2)
        resp[:headers][key] = ([*resp[:headers][key]] << value).compact.join(', ')
        if key.casecmp('Content-Length') == 0
          content_length = value.to_i
        elsif (key.casecmp('Transfer-Encoding') == 0) && (value.casecmp('chunked') == 0)
          transfer_encoding_chunked = true
        end
      end

      unless req =~ /^CONNECT/ || req =~ /^HEAD/ || UFuzz::NO_ENTITY.include?(resp[:status])
        if transfer_encoding_chunked
          while (chunk_size = socket.readline.chop!.to_i(16)) > 0
            resp[:body] << socket.read(chunk_size + 2).chop! # 2 == "/r/n".length
          end
          socket.read(2) # 2 == "/r/n".length
        elsif remaining = content_length
          while remaining > 0
            resp[:body] << socket.read([config.chunk_size, remaining].min)
            remaining -= config.chunk_size
          end
        else
          resp[:body] << socket.read
        end
      end
    rescue => e
      log "error parsing response - #{e.message}", DEBUG
      log e.backtrace, TRACE
    end
    
    self.new(resp)
  end
  
end

end
end
  
  
