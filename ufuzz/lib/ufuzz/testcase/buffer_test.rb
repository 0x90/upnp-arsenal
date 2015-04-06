module UFuzz

class BufferTest < TestCase
  def initialize(opts = {})
    @series = opts[:series] || 'A'
    @start  = opts[:start]  || 32
    @step   = opts[:step]   || :exponential
    @limit  = opts[:limit]  || 18000
    super
  end
  
  def threadable?
    false
  end
  
  def test(content)
    @monitor.check ? Fault.new('buffer overflow', 'possible buffer overflow', @monitor.crash_dump) : nil
  end
  
  def update_transforms
    @transforms = [ proc {|a| a.join.to_s } ]
  end
  
  private
    
  def init_block
    if @series.respond_to? :each
      @repeatables = @series
    else
      @repeatables = Array(@series)
    end
    
    @block = Fiber.new do
      @repeatables.each do |r|
        if @step == :exponential
          n = 0
          loop do
            i = @start + (2 ** n + 1)
            i = @limit if i > @limit
            Fiber.yield( @transforms.inject(Array.new(i,r)) { |v,proc| v = proc.call(v) } )
            break if i == @limit
            n += 1
          end
        else
          (@start..@limit).step(@step) do |i|
            next if i == 0
            Fiber.yield( @transforms.inject(Array.new(i,r)) { |v,proc| v = proc.call(v) } )
          end
        end
      end
      nil
    end
  end
  
end

end