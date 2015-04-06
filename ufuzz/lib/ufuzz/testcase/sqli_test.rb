module UFuzz

class SqliTest < TestCase
  def initialize(opts = {})
    @limit  = opts[:limit] || -1
    @vals   = File.read(File.expand_path(File.join(
                File.dirname(__FILE__), '..', 'wordlist', 'sql_injection.txt')))
              
    super
  end

  def threadable?
    true
  end

  def test(content)
    delay = Time.now.to_f - @time
    if delay >= Config.instance.detect_delay
      Fault.new('sql injection', "possible sql injection - #{@current.inspect}: delay #{delay}")
    else
      nil
    end
  end

  def update_transforms
    @transforms = [ proc {|a| a.to_s } ]
    add_context_transforms
  end

  private
  
  def init_block
    @block = Fiber.new do
      @vals.each_line do |val|
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