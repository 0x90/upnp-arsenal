module UFuzz
  
class Fault
  attr_accessor :reason, :desc, :crash_dump, :tx, :rx
  
  def initialize(reason, desc, crash_dump = nil)
    @reason     = reason
    @desc       = desc
    @crash_dump = crash_dump
    @tx         = nil
    @rx         = nil
  end
  
  def pretty_print(opts = {})
    "#{reason} - #{desc}"
  end
end

end