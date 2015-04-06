module UFuzz

class TestCase
  def initialize(opts = {})
    @opts     = opts
    @monitor  = opts[:monitor]
    @time     = Time.now.to_f
    @data     = opts[:data].to_s
    
    raise(SyntaxError, "A monitor must be supplied") if @monitor.nil?
    
    update_transforms
    init_block
    @alive = true
    @cache = @block.resume
  end

  def next?
    @alive
  end
  
  def finished?
    !@alive
  end

  def next
    @current = @cache
    begin
      @cache = @block.resume
    rescue FiberError
      @cache = false
    end
    @alive = false unless @cache
    @time = Time.now.to_f
    self
  end
  
  def to_s
    @current.to_s
  end
  
  def inspect
    self.class
  end

  def to_a
    a = []
    a << self.next while self.next?
    self.rewind
    a
  end
  
  def each(&blk)
    blk.yield self.next while self.next?
    self.rewind
  end

  def rewind(data = nil)
    initialize(@opts.merge(:data => data))
    true
  end
  
  def threadable?
    true
  end
  
  def test(content)
    raise NotImplementedError
  end
  
  def update_transforms
  end
  
  def init_block
  end
  
  def add_context_transforms
    if @data.match(/^[0-9\.\-]+$/)
      @transforms
    elsif @data.match(/^[A-Z0-9]+$/) && @data.length > 7
      @transforms << proc {|a| a.to_s.hexify.upcase }
    elsif @data.match(/^[a-z0-9]+$/) && @data.length > 7
      @transforms << proc {|a| a.to_s.hexify }
    elsif @data.match(/^[a-zA-Z0-9+\/]+={0,2}$/) && @data.length > 11
      @transforms << proc {|a| a.to_s.b64 }
    end
  end
end

class TestCaseChain < TestCase
  def initialize(*test_cases)
    @opts       = test_cases
    @test_cases = test_cases
    
    init_block
    
    @alive = true
    @cache = @block.resume
  end

  def rewind(data=nil)
    @test_cases.each { |t| t.rewind(data) }
    initialize(*@opts)
    true
  end
  
  def next
    @current = @cache
    begin
      @cache = @block.resume
    rescue FiberError
      @cache = false
    end
    @alive = false unless @cache
    @current
  end
  
  def init_block
    @block = Fiber.new do
      @test_cases.each do |t|
        while t.next?
          Fiber.yield t
          t.next
        end
      end
      false
    end
  end
end

end