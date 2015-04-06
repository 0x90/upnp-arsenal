module UFuzz

class FmtTest < TestCase
  def initialize(opts = {})
    @limit  = opts[:limit] || -1
    @vals   = File.read(File.expand_path(File.join(
                File.dirname(__FILE__), '..', 'wordlist', 'format_string.txt')))
                
    super
  end
  
  def threadable?
    false
  end
  
  def test(content)
    @monitor.check ? Fault.new('format string', "possible fmt string vuln - #{@current.inspect}", @monitor.crash_dump) : nil
  end
  
  def update_transforms
    @transforms = [ proc {|a| a.to_s } ]
    add_context_transforms
  end
  
  private
    
  def init_block
    @block = Fiber.new do
      @vals.each_line do |val|
        begin
          val = eval('"' + val + '"')
        rescue SyntaxError
          log "Error in wordlist: #{val.inspect}", WARN
        end
        val.chomp!
        @transforms.each do |t|
          Fiber.yield( t.call(val) )
        end
      end
      nil
    end
  end
  
end

end