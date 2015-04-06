module UFuzz
module Http
  
class Session
  attr_accessor :cookies, :config, :connection, :request, :response, :config
  
  def initialize(c)
    @config     = c
    @connection = c.create_connection
    @request    = c.create_request
    @response   = nil
    @cookies    = CookieJar.new(@request)
  end

  def session_cookie
    raise NotImplementedError
  end
  
  def login
    raise NotImplementedError
  end
  
  def logout
    raise NotImplementedError
  end
  
  def check
    raise NotImplementedError
  end
  
  def logged_out
    raise NotImplementedError
  end
    
  def create
    log "#{caller.first.match(/`(.+)'/) { |m| m[1] }} -> creating new session", DEBUG
    @response = @connection.send(Request.new(login))
    @cookies.parse @response
  end
  
  def clear
    log "#{caller.first.match(/`(.+)'/) { |m| m[1] }} -> invalidating session", DEBUG
    @response = @connection.send(Request.new(logout).update_cookies(self))
    @cookies.parse @response
  end
  
  def session_cookies
    @cookies.find(session_cookie)
  end
  
  def valid?
    req = Request.new(check).update_cookies(self)
    resp = @connection.send(req)
    
    if logged_out.is_a? Integer
      return !(resp.status == logged_out)
    elsif logged_out.is_a? Regexp
      return !(resp.body =~ logged_out)
    else
      return !(resp.body =~ /#{logged_out}/)
    end
    true
  end
end

end
end