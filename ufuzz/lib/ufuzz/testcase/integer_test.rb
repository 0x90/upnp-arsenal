module UFuzz

class IntegerTest < TestCase
  def initialize(opts = {})
    @series = opts[:series] || 'A'
    @start  = opts[:start]  || 16
    @step   = opts[:step]   || :exponential
    @limit  = opts[:limit]  || 32768
    super
  end
  
  def threadable?
    false
  end
  
  def test(content)
    @monitor.check ? Fault.new('integer overflow', 'possible integer overflow', @monitor.crash_dump) : nil
  end
  
  def update_transforms
    @transforms = [ proc {|a| a.to_s } ]
    if @data.match(/^[A-Z0-9]+$/)
      @transforms << proc {|a| ("%x" % a.to_i).upcase }
    elsif @data.match(/^[a-z0-9]+$/)
      @transforms << proc {|a| "%x" % a.to_i }
    end
  end
  
  private
  
  def init_block
    cases = []
    
    [ 32 ].each do |bitlength|
      # full and empty
      cases << ('1' * bitlength).to_i(2)
      cases << ('0' * bitlength).to_i(2)
    
      # flip up to 4 bits at each end
      # depending on bitlength
      case
      when bitlength > 32
        lim = 4
      when (16..32) === bitlength
        lim = 3
      when (8..15) === bitlength
        lim = 2
      else
        lim = 1
      end
    
      for i in (1..lim) do
        cases << (('1' * i) + ('0' * (bitlength - i))).to_i(2)
        cases << (('0' * (bitlength - i)) + ('1' * i)).to_i(2)
        cases << (('0' * i) + ('1' * (bitlength - i))).to_i(2)
        cases << (('1' * (bitlength - i)) + ('0' * i)).to_i(2)
      end
    
      # alternating
      cases << ('1'*bitlength).gsub(/11/,"10").to_i(2)
      cases << ('0'*bitlength).gsub(/00/,"01").to_i(2)
    end

    @block = Fiber.new do
      # The call to uniq avoids repeated elements
      # when bitlength < 4
      cases.uniq.each { |c| Fiber.yield c }
      nil
    end
  end
  
end

end