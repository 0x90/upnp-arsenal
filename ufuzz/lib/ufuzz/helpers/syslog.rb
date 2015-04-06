module UFuzz
module MonitorHelpers
  
module SyslogServer
  def messages
    @messages
  end
  
  def clear_messages
    @messages = nil
  end
  
  def receive_data(data)
    if @messages
      @messages += data + "\n"
    else
      @messages = data + "\n"
    end
  end
end

module SyslogHelper
  def start(opts = {})
    listen_host = (opts[:syslog_listen_host] || '172.16.8.1') 
    listen_port = (opts[:syslog_listen_port] || 9514).to_i
    @syslog_em = nil
    @syslog_thread = Thread.new {
      EM::run do
        @syslog_em = EM.open_datagram_socket listen_host, listen_port, UFuzz::Helpers::SyslogServer
      end
    }
  end
  
  def read
    msgs = @syslog_em.messages
    @syslog_em.clear_messages
    msgs
  end
  
  def stop
    @syslog_thread.kill
  end
end

end
end
