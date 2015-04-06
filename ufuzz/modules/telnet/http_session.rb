class TelnetSession < UFuzz::Http::Session
  def login
    post_string = "ajax=1&username=#{config.username}&secretkey=#{config.password}"
    "POST /logincheck HTTP/1.1\r\n" +
    "Host: #{connection.host}\r\n" + 
    "Content-Type: text/plain; charset=UTF-8\r\n" +
    "Content-Length: #{post_string.length}\r\n\r\n" +
    post_string
  end
  
  def logout
    "GET /logout HTTP/1.1\r\n" +
    "Host: #{connection.host}\r\n" +
    "Accept: text/html\r\n\r\n"
  end
  
  def check
    "GET /index HTTP/1.1\r\n" +
    "Host: #{connection.host}\r\n" +
    "Accept: text/html\r\n\r\n"
  end
  
  def logged_out
    /login_panel/
  end
  
  def session_cookie
    @@session_cookie ||= "#{@response}".match(/APSCOOKIE_[0-9]+/) {|m| m[0]}
  end
end