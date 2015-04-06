class TelnetMonitor < UFuzz::Monitor
  include UFuzz::MonitorHelpers::Telnet
  
  def start
    login
    telnet_cmd('diag debug crash clear')
  end
  
  def check
    telnet_cmd('diag debug crash read') do |c|
      if c && c.length > 300
        @crash_dump = c.dup
        telnet_cmd('diag debug crash clear')
        return c
      elsif c && c.length > 80
        telnet_cmd('diag debug crash clear')
      end
    end
    @crash_dump = nil
    return nil
  end
  
  def close
    telnet_cmd('diag debug crash clear')
    telnet_cmd('exit')
  end
end
