class SerialMonitor < UFuzz::Monitor
  def start
    @index = 0
    @log = ''
    @sp = SerialPort.new("/dev/tty.usbserial-A600e1dU", 38400)
    
    t = Thread.new {
      loop do
        c = @sp.getc
        print c
        @log += c
      end
    }
  end
  
  def check
    curr_length = @log.length
    if @log[@index..-1] =~ /SIGSEGV/
      sleep(10)
      @log.length > 1000 ? @crash_dump = @log[-1000..-1].dup : @crash_dump = @log[@index..-1].dup
      @index = curr_length
      log "Reboot Detected, pausing...", WARN
      sleep(30)
      log "Resuming...", WARN
      return @crash_dump
    else
      @crash_dump = nil
      return nil
    end
  end
  
  def close
    @sp.close
  end
end