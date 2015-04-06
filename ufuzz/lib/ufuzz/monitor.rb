module UFuzz

class Monitor
  attr_accessor :config, :crash_dump, :session
  
  def initialize(config)
    @config = config
    start
  end
  
  def start
  end
  
  def close
  end
  
  def check
  end
end

end