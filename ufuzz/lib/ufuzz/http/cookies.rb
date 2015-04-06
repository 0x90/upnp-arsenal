module UFuzz
module Http

class CookieJar
  attr_accessor :cookies
  
  def initialize(data = nil)
    @cookies = {}
    if data.is_a? Hash
      @cookies = data
    else
      parse(data)
    end
  end
  
  def to_s
    @cookies.each_pair.map { |k,v| "#{k}=#{v}" }.join('; ')
  end
  
  def inspect
    "<#{"%x" % self.object_id} #{self.class}> #{cookies.inspect}"
  end
  
  def to_h
    @cookies
  end
  
  def to_hash
    @cookies
  end
  
  def merge(h)
    @cookies.merge!(h)
  end
  
  def find(c)
    if @cookies[c]
      return { c => @cookies[c] }
    else
      return { }
    end
  end
  
  def empty?
    @cookies.empty?
  end
  
  def parse(data)
    if data.is_a? Response
      parse_from_resp(data)
    else
      parse_from_req(data.to_s)
    end
  end
  
  def parse_from_resp(resp)
    set_cookie = []
    
    set_cookie << resp.headers['Set-Cookie'] if resp.headers['Set-Cookie']
    set_cookie << resp.headers['Set-cookie'] if resp.headers['Set-cookie']

    set_cookie.each do |sc|
      sc.split(/[;,]\s*/).each do |c|
        pair = c.split('=', 2)
        next if pair.count != 2 || ['expires', 'path'].include?(pair[0])
        update_cookie_raw(c)
      end
    end
  end
  
  def parse_from_req(req)
    req.match(/Cookie: ([^\r\n]+)/) do |m|
      cookie_header = m[1]
      cookie_header.split(/[;,]\s?/).each do |c|
        update_cookie_raw(c)
      end
    end
  end
  
  def update_cookie_raw(c)
    pair = c.split("=", 2)
    return nil unless pair.count == 2
    @cookies.merge!({pair[0] => pair[1]})
  end
  
end

end
end