module UFuzz
module Validator
  def validate(config)
    unless config.module
      log "no module specified, assuming generic", WARN
      config.module = 'generic'
    end

    unless config.host || config.upnp
      log "No target host specified, use -t to define target IP", FAIL
      exit
    end
  
    unless config.import || config.upnp
      log "No request or input file specified, use -i <burp.xml> or --upnp", FAIL
      exit
    end
  
    unless config.app
      config.app = 'http'
    end

    unless config.port || config.upnp
      if config.app == 'http'
        log "no port specified, assuming tcp port 80", WARN
        config.port = 80
      end
    end
  end
end
end 