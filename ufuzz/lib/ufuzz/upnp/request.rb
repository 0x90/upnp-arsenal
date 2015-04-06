module UFuzz
module UPnP

class Request
  attr_accessor :ip, :port, :csock, :ssock, :enum_hosts
  
  DEFAULT_IP = "239.255.255.250"
  DEFAULT_PORT = 1900
  UPNP_VERSION = '1.0'
  MAX_RECV = 8192
  VERBOSE = nil
  UNIQ = nil
  DEBUG = nil
  LOG_FILE = nil
  IFACE = nil

  def initialize(ip = nil, port = nil, iface = nil, app_cmds = [])
    @msearch_headers = {
      'MAN' => '"ssdp:discover"',
      'MX'  => '2'
    }
    
    init_sockets(ip, port, iface)
    @http_headers = []
    @enum_hosts = {}
    @soap_end = /<\/.*:envelope>/
  end
  
  def init_sockets(ip, port, iface)
    @csock.close if @csock && !@csock.closed?
    @ssock.close if @ssock && !@ssock.closed?
    
    @iface = iface
    @ip    = (ip || DEFAULT_IP)
    @port  = (port || DEFAULT_PORT)
    
    @csock = UDPSocket.open
    @csock.setsockopt Socket::IPPROTO_IP, Socket::IP_TTL, 2
    
    @ssock = UDPSocket.open
    @ssock.setsockopt Socket::SOL_SOCKET, Socket::SO_REUSEADDR, 1
    @ssock.setsockopt Socket::IPPROTO_IP, Socket::IP_ADD_MEMBERSHIP, 
                      IPAddr.new(@ip).hton + Socket.gethostbyname(Socket.gethostname)[3]
    @ssock.bind Socket::INADDR_ANY, @port
  end
  
  def cleanup
    @csock.close
    @ssock.close
  end
  
  def send_udp(data, socket = nil)
    socket = @csock unless socket
    socket.send(data, 0, @ip, @port)
  end
  
  def listen_udp(size, socket = nil)
    socket = @ssock unless socket
    socket.recv(size)
  end
  
  def local_ip
    IPAddr.new_ntoh(Socket.gethostbyname(Socket.gethostname)[3]).to_s
  end
  
  def create_new_listener(ip = local_ip, port = DEFAULT_PORT)
    newsock = UDPSocket.new(Socket::AF_INET)
    newsock.setsockopt(Socket::SOL_SOCKET, Socket::SO_REUSEADDR, 1)
    newsock.bind(ip, port)
    newsock
  end
  
  def listener
    @ssock
  end
  
  def sender
    @csock
  end
  
  def parse_url(url)
    delim = '://'
    host = nil
    page = nil
    
    begin
      (host,page) = url.split(delim)[1].split('/', 2)
      page = '/' + page
    rescue
      #If '://' is not in the url, then it's not a full URL, so assume that it's just a relative path
      page = url
    end

    [host, page]
  end
  
  def parse_device_type_name(str)
    delim1 = 'device:'
    delim2 = ':'

    if str.include?(delim1) && !str.end_with?(delim2)
      str.split(delim1)[1].split(delim2, 2)[0]
    else
      nil
    end
  end
  
  def parse_service_type_name(str)
    delim1 = 'service:'
    delim2 = ':'

    if str.include?(delim1) && !str.end_with?(delim2)
      str.split(delim1)[1].split(delim2, 2)[0]
    else
      nil
    end
  end
  
  def parse_header(data, header)
    delimiter = "#{header}:"

    lower_delim = delimiter.downcase
    data_array = data.split("\r\n")

    #Loop through each line of the headers
    data_array.each do |line|
      lower_line = line.downcase
      #Does this line start with the header we're looking for?
      if lower_line.start_with?(lower_delim)
        return line.split(':', 2)[1].strip
      end
    end
    nil
  end

  def extract_single_tag(data, tag)
    start_tag = "<%s" % tag
    end_tag   = "</%s>" % tag

    tmp = data.split(start_tag)[1]
    index = tmp.index('>')
    if index
      index += 1
      return tmp[index..-1].split(endTag)[0].strip
    end
  rescue Exception => e
    puts e.message
    puts e.backtrace
    nil
  end
  
  def parse_ssdp_info(data)
    host_found = nil
    message_type = nil
    xml_file = nil
    host = nil
    upnp_type = nil
    known_headers = {
      "NOTIFY" => 'notification',
      "HTTP/1.1 200 OK" => 'reply'
    }
    
    known_headers.each_pair do |text, msg_type|
      if data.upcase.start_with? text
        message_type = msg_type
        break
      end
    end
    
    return nil unless message_type
    
    #Get the host name and location of it's main UPNP XML file
    xml_file = parse_header(data, 'LOCATION')
    upnp_type = parse_header(data, 'SERVER')
    host, page = parse_url(xml_file)
    
    #Sanity check to make sure we got all the info we need
    unless xml_file && host && page
      puts "Error parsing header:"
      puts data
      return nil
    end
    
    #Get the protocol in use (i.e., http, https, etc)
    protocol = xml_file.split('://')[0] + '://'
    
    #Check if we've seen this host before; add to the list of hosts if:
    #  1. This is a new host
    #  2. We've already seen this host, but the uniq hosts setting is disabled
    @enum_hosts.each_pair do |host_id, host_info|
      if host_info[:name] == host
        host_found = true
        return nil
      end
    end
    
    index = @enum_hosts.length
    @enum_hosts[index] = {
      name: host,
      data_complete: nil,
      proto: protocol,
      xml_file: xml_file,
      server_type: nil,
      upnp_server: upnp_type,
      device_list: {}
    }
    
    log "SSDP #{message_type} message from #{host}", INFO
    log("XML file is located at #{xml_file}", INFO) if xml_file
    log("Device is running #{upnp_type}", INFO) if upnp_type
  end
  
  def get_xml(url)
    headers = {
      'USER-AGENT' => "uPNP/#{UPNP_VERSION}",
      'CONTENT-TYPE' => 'text/xml; charset="utf-8"'
    }
    
    resp = ::Net::HTTP.get_response(URI(url))
    output = resp.body
    headers = {}
    resp.to_hash.each_pair { |k,v| headers[k] = (v.first rescue '') }
    [headers, output]
  end
  
  def build_soap_request(hostname, service_type, control_url, action_name, action_args = {})
    arg_list = ''
    
    if control_url.include? '://'
      url_array = control_url.split('/', 4)
      if url_array.length < 4
        control_url = '/'
      else
        control_url = '/' + url_array[3]
      end
    end
    
    soap_request = "POST #{control_url} HTTP/1.1\r\n"
    
    if hostname.include? ':'
      hostname_array = hostname.split(':')
      host = hostname_array[0]
      port = hostname_array[1].to_i
    else
      host = hostname
      port = 80
    end
    
    action_args.each_pair do |arg, value|
      arg_list += "<#{arg}>#{value}</#{arg}>"
    end
    
    soap_body = <<-EOS
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:#{action_name} xmlns:u="#{service_type}">
   #{arg_list}
  </u:#{action_name}>
 </s:Body>
</s:Envelope>
EOS
    
    headers = {
      'Content-Type'    => 'text/xml; charset="utf-8"',
      'SOAPACTION'      => "\"#{service_type}##{action_name}\"",
      'Content-Length'  => soap_body.length,
      'HOST'            => hostname,
      'User-Agent'      => 'CyberGarage-HTTP/1.0',
    }
    
    headers.each_pair do |head, value|
      soap_request += "#{head}: #{value}\r\n"
    end
    soap_request += "\r\n#{soap_body}"
    
    soap_request
  end
  
  def send_soap(hostname, service_type, control_url, action_name, action_args)
    soap_response = ''
    
    soap_request = build_soap_request(hostname, service_type, control_url, action_name, action_args)
    
    sock = TCPSocket.new host, port
    sock.write(soap_request)
    
    data = ''
    begin
      Timeout.timeout(10) do
        loop {
          data = (sock.readpartial(1024) rescue nil)
          break if data.nil?
          soap_response += data
          break if soap_response =~ @soap_end
        }
      end
      sock.close
      
      header, body = soap_response.split("\r\n\r\n", 2)
      if !header.upcase.start_with?('HTTP/1.1 200')
        puts "SOAP request failed with error code: #{header.split("\r\n")[0].split(' ', 2)[1]}"
        error_msg = extract_single_tag(body, 'errorDescription')
        puts "SOAP error message: #{error_msg}" if error_msg
        return nil
      else
        return body
      end
    rescue Exception => e
      log "caught exception in send_soap:", FAIL
      puts e.message
      puts e.backtrace
      sock.close
      return nil
    end
  end
    
  def get_host_info(xml_data, xml_headers, index)
    if index >= 0 && index < @enum_hosts.length
      xml_root = Nokogiri::XML.parse(xml_data).root
      parse_device_info(xml_root, index)
      @enum_hosts[index][:server_type] = xml_headers['server']
      @enum_hosts[index][:data_complete] = true
      true
    else
      nil
    end
  end
  
  def parse_device_info(xml_root, index)
    device_entry_pointer = {}
    dev_tag = 'device'
    device_type = 'deviceType'
    device_list_entries = 'deviceList'
    device_tags = [
      "friendlyName",
      "modelDescription",
      "modelName",
      "modelNumber",
      "modelURL",
      "presentationURL",
      "UDN",
      "UPC",
      "manufacturer",
      "manufacturerURL"
    ]
    
    xml_root.css(dev_tag).each do |device|
      device_type_name = (device.css(device_type).children.first.content rescue nil)
      next unless device_type_name
      
      device_display_name = parse_device_type_name(device_type_name)
      next unless device_display_name
      
      device_entry_pointer = @enum_hosts[index][:device_list][device_display_name] = {}
      device_entry_pointer['fullName'] = device_type_name
      
      device_tags.each do |tag|
        device_entry_pointer[tag] = (device.css(tag).children.first.content rescue '')
      end
      
      parse_service_list(device, device_entry_pointer, index)
    end
  end
  
  def parse_service_list(xml_root, device, index)
    service_entry_pointer = nil
    dict_name = :services
    service_list_tag = "serviceList"
    service_tag = "service"
    service_name_tag = "serviceType"
    service_tags = [
      "serviceId",
      "controlURL",
      "eventSubURL",
      "SCPDURL"
    ]
        
    device[dict_name] = {}
    # Get a list of all services offered by this device
    
    xml_root.css(service_tag).each do |service|
      service_name = (service.css(service_name_tag).children.first.content rescue nil)
      next unless service_name
      
      service_display_name = parse_service_type_name(service_name)
      next unless service_display_name
      
      service_entry_pointer = device[dict_name][service_display_name] = {}
      service_entry_pointer['fullName'] = service_name
      
      service_tags.each do |tag|
        service_entry_pointer[tag] = service.css(tag).children.first.content
      end

      parse_service_info(service_entry_pointer, index)
    end
  end
  
  def parse_service_info(service, index)
    arg_index = 0
    arg_tags = ['direction', 'relatedStateVariable']
    action_list = 'actionList'
    action_tag = 'action'
    name_tag = 'name'
    argument_list = 'argumentList'
    argument_tag = 'argument'
    
    xml_file = @enum_hosts[index][:proto] + @enum_hosts[index][:name]
    if !xml_file.end_with?('/') && !service['SCPDURL'].start_with?('/')
      xml_file += '/'
    end
    
    if service['SCPDURL'].include? @enum_hosts[index][:proto]
      xml_file = service['SCPDURL']
    else
      xml_file += service['SCPDURL']
    end
    
    service['actions'] = {}
    
    xml_headers, xml_data = get_xml(xml_file)
    
    unless xml_data
      log "could not get service descriptor at: #{xml_file}", WARN
      return nil
    end
    
    xml_root = Nokogiri::XML.parse(xml_data).root
    
    action_list = xml_root.css(action_list)
    actions = action_list.css(action_tag)
    
    actions.each do |action|
      action_name = action.css(name_tag).children.first.content.strip
      
      service['actions'][action_name] = {}
      service['actions'][action_name]['arguments'] = {}
      
      arg_list = action.css(argument_list)
      arguments = arg_list.css(argument_tag)
      
      arguments.each do |argument|
        arg_name = (argument.css(name_tag).children.first.content rescue nil)
        next unless arg_name
        service['actions'][action_name]['arguments'][arg_name] = {}
        
        arg_tags.each do |tag|
          service['actions'][action_name]['arguments'][arg_name][tag] = argument.css(tag).children.first.content
        end
      end
    end
    
    parse_service_state_vars(xml_root, service)
  end
  
  def parse_service_state_vars(xml_root, service_pointer)
    na = 'N/A'
    var_vals = ['sendEvents','dataType','defaultValue','allowedValues']
    service_state_table = 'serviceStateTable'
    state_variable = 'stateVariable'
    name_tag = 'name'
    data_type = 'dataType'
    send_events = 'sendEvents'
    allowed_value_list = 'allowedValueList'
    allowed_value = 'allowedValue'
    allowed_value_range = 'allowedValueRange'
    minimum = 'minimum'
    maximum = 'maximum'
    
    service_pointer['serviceStateVariables'] = {}
    
    begin
      state_vars = xml_root.css(service_state_table).first.css(state_variable)
    rescue
      return false
    end
    
    state_vars.each do |var|
      var_vals.each do |tag|
        begin
          var_name = var.css(name_tag).children.first.content
        rescue
          log "failed to get state variable name for service #{service_pointer['fullName']}", WARN
          next
        end
        
        service_pointer['serviceStateVariables'][var_name] = {}
        
        service_pointer['serviceStateVariables'][var_name]['dataType'] = (var.css(data_type).children.first.content rescue na)
        service_pointer['serviceStateVariables'][var_name]['sendEvents'] = (var.css(send_events).children.first.content rescue na)
        service_pointer['serviceStateVariables'][var_name][allowed_value_list] = []
        
        begin
          vals = var.css(allowed_value_list).first.css(allowed_value)
          
          vals.each do |val|
            service_pointer['serviceStateVariables'][var_name][allowed_value_list] << val.children.first.content
          end
        rescue
        end
        
        begin
          val_list = var.css(allowed_value_range)
        rescue
          next
        end
        
        service_pointer['serviceStateVariables'][var_name][allowed_value_range] = []
        begin
          service_pointer['serviceStateVariables'][var_name][allowed_value_range] << val_list.css(minimum).first.children.content
          service_pointer['serviceStateVariables'][var_name][allowed_value_range] << val_list.css(maximum).first.children.content
        rescue
        end
      end
    end
    
    true
  end
  
  def msearch(timeout = 10)
    default_st = 'upnp:rootdevice'
    st = 'schemas-upnp-org'
    myip = local_ip
    lport = @port
    
    st = default_st
    
    request = "M-SEARCH * HTTP/1.1\r\n" +
              "HOST:#{@ip}:#{@port}\r\n" +
              "ST:#{st}\r\n"
    
    @msearch_headers.each_pair do |header, value|
      request += "#{header}:#{value}\r\n"
    end
    request += "\r\n"
    
    log "discovering UPnP devices", INFO
    
    server = create_new_listener(myip, lport)
    unless server
      puts "failed to bind to port #{lport}"
      return nil
    end
    
    send_udp(request, server)
    begin
      Timeout.timeout(timeout) do
        loop {
          data = listen_udp(1024, server)
          parse_ssdp_info(data)
        }
      end
    rescue Timeout::Error
      log "finished discovery mode", INFO
      server.close
    end
  end
  
  def enumerate(index = nil)
    if index
      enum_host(@enum_hosts[index])
    else
      @enum_hosts.each_pair do |index, host|
        enum_host(index, host)
      end
    end
  end
  
  def enum_host(index, host_info)
		log "Requesting device and service info for #{host_info[:name]} (this could take a few seconds)", INFO
		xml_headers, xml_data = get_xml host_info[:xml_file]

		unless xml_data
			log "Failed to request host XML file: #{host_info[:xml_file]}", WARN
      return nil
    end

		unless get_host_info(xml_data, xml_headers, index)
			log "Failed to get device/service info for #{host_info[:name]}"
			return nil
    end
    
		log "Host data enumeration complete for #{host_info[:name]}", INFO
  end
  
  def generate_requests(index = nil)
    requests = []
    
    if index
      gen_host_requests(@enum_hosts[index])
    else
      @enum_hosts.each_pair do |index, host|
        requests += gen_host_requests(index, host)
      end
    end
    
    requests
  end
  
  def gen_host_requests(index, host)
    requests = []
    hostname = host[:name]
    
    host[:device_list].each_pair do |device_name, device|
      device[:services].each_pair do |service_name, service|
        service['actions'].each_pair do |action_name, action|
          arg_list = {}
          index = 0
          action['arguments'].each_pair do |arg_name, argument|
            if argument['direction'] && argument['direction'].include?('in')
              arg_list[arg_name] = "$PARAM_#{index}_$"
              index += 1
            end
          end
              
          requests << build_soap_request(hostname, service['fullName'], service['controlURL'], action_name, arg_list)
        end
      end
    end
    
    requests
  end
end

end  
end  












      