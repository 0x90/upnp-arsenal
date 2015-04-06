module UFuzz
module Http

class Request
  attr_accessor :request
  
  def initialize(req)
    @request = req.dup
    @config  = Config.instance
    if @config.fixhost
      @request.gsub!(/^[hH]ost: (.+)$/) do |g|
        "Host: #{@config.host}"
      end
    end
  end
  
  def to_s
    request
  end
  
  def inspect
    "<#{"%x" % self.object_id} #{self.class}> #{request.inspect}"
  end
  
  def post?
    first_line =~ /^POST/
  end
  
  def get?
    first_line =~ /^GET/
  end
  
  def body
    request.scan(/(\r\n\r\n|\n\n)([^\r^\n]+)/).flatten.last
  end
  
  def body=(params)
    if params.is_a? Hash
      params = params.each_pair.map { |k,v| "#{k}=#{v}" }.join('&')
    end
    @request.gsub!(/(\r\n\r\n|\n\n)([^\r^\n]+)/, "\r\n\r\n" + params)
    update_content_length
  end
  
  def first_line
    request.split(/\r\n|\n/)[0]
  end
  
  def path
    first_line.match(/^[\w]+ ([^ \?]+)/) { |m| m[1] }
  end
  
  def path=(new_path)
    @request.gsub!(/\A.*(\r\n|\n)/) do |g|
      crlf = $1.dup
      if query_string
        "#{verb} #{new_path}?#{query_string} HTTP/1.1#{crlf}"
      else
        "#{verb} #{new_path} HTTP/1.1#{crlf}"
      end
    end
  end
  
  def uri
    first_line.match(/^[\w]+ ([^ ]+)/) { |m| m[1] }
  end
  
  def verb
    first_line.match(/^([\w]+) /) { |m| m[1] }
  end
  
  def body_variables
    body.split('&').inject({}) do |r, v|
      h = v.split('=')
      h << '' if h.count < 2
      r.merge!({h[0] => h[1]}) if h.count > 1
      r
    end
  end
  
  def query_string
    first_line.match(/.*\?(.*) /) { |m| m[1] }
  end
  
  def headers
    req = @request.split(/\r\n\r\n|\n\n/)[0]
    req.split(/\r\n|\n/)[1..-1].inject({}) do |r, h|
      pair = h.split(": ", 2)
      r.merge!({pair[0] => pair[1]}); r
    end
  end
  
  def set_header(header, value)
    if @request.include? "#{header}: "
      @request.gsub!(/^#{header}: .*(\r\n|\n)/) do |g|
        "#{header}: #{value}\r\n"
      end
    else
      index = (@request =~ /\r\n\r\n|\n\n/)
      @request.insert(index, "\r\n#{header}: #{value}")
    end
  end
  
  def query_string=(params)
    if params.is_a? Hash
      params = params.each_pair.map { |k,v| "#{k}=#{v}" }.join('&')
    end
    @request.gsub!(/\A.*(\r\n|\n)/) do |g|
      crlf = $1.dup
      "#{verb} #{path}?#{params} HTTP/1.1#{crlf}"
    end
  end
  
  def url_variables
    return {} if query_string.nil?
    query_string.split('&').inject({}) do |r, v|
      h = v.split('=')
      h << '' if h.count < 2
      r.merge!({h[0] => h[1]}) if h.count > 1
      r
    end
  end
  
  def verb=(new_verb)
    @request.gsub!(/\A[A-Z]+/, new_verb)
  end
  
  def verb_path
    "#{verb} #{path}"
  end
  
  def verb_uri
    "#{verb} #{uri}"
  end
  
  def summary
    "#{first_line} #{@request.length} bytes"
  end
  
  def sanitized_path
    verb_uri.gsub(/(.){20,}/, '\1....\1').gsub(/(..){10,}/, '\1....\1')
  end
  
  def update_content_length
    if post?
      length = @request.split("\r\n\r\n")[1].length rescue nil
      length = @request.split("\n\n")[1].length if length.nil?
      @request.gsub!(/Content-Length: [0-9]+/i, "Content-Length: #{length}")
    end
    self
  end
  
  def update_cookies(sess)
    @cookies = CookieJar.new(self)
    @cookies.merge(sess.session_cookies)
    
    unless @cookies.empty?
      log "cookies: #{@cookies}", TRACE
      if @request =~ /Cookie: /i
        @request.gsub!(/^Cookie: ([^\r^\n]*)/i, "Cookie: #{@cookies}")
      else
        apos = (@request =~ /Accept: /i)
        @request.insert(apos, "Cookie: #{@cookies}\r\n") if apos && apos > 0
      end
    end
    self
  end
  
end

end
end
  
  
  