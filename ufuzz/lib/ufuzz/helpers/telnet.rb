module UFuzz
module MonitorHelpers
  
module Telnet
  def login
    @session = ::Net::Telnet::new("Host" => (config.monitor_host || config.host), "Prompt" => (config.prompt || /[a-zA-Z0-9]+ # \z/in))
    @session.login(config.admin_user, config.admin_pass)
  rescue Errno::ETIMEDOUT, Timeout::Error => e
    log "could not connect to target via telnet", FAIL
    log e.backtrace, DEBUG
    exit
  end

  def telnet_cmd(cmd, &block)
    if block_given?
      @session.cmd(cmd, &block)
    else
      @session.cmd(cmd)
    end
  rescue Errno::ETIMEDOUT, Timeout::Error => e
    log "telnet logged out, retrying", FAIL
    log e.backtrace, DEBUG
    login
  end
end

end
end