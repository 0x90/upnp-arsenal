# -*- coding: binary -*-
module UFuzz
module Http
  
class Connection
  attr_accessor :host, :port, :ssl, :socket, :config, :connected
  
  def initialize(c)
    @config = c
    @host   = c.host
    @port   = c.port.to_i
    @ssl    = c.ssl
    @socket = nil
    @connected = false
  end
  
  def send(req, opts = {})
    resp    = nil
    @socket = nil
    retr    = 0
    @connected = false
    
    begin
      if @ssl
        @socket = UFuzz::Net::SSLSocket.new(@config)
      else
        @socket = UFuzz::Net::Socket.new(@config)
      end
      
      @connected = true
      @socket.write(req.to_s)
      resp = Response.parse(@socket, req.to_s)

    rescue => e
      log e.message, DEBUG
      @socket.close if @socket
      if e.message == 'Connection refused - connect(2)'
        sleep(0.5)
        retr += 1
        if retr <= @config.retry_limit
          retry
        end
      end
    end
    
    @socket.close if @socket
    resp
  end
  
  def connection_success?
    @connected
  end
end

end
end
    