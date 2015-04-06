require 'optparse'

module UFuzz
module Options
  def parse_options(cmd_line)
    options = {}

    optparse = OptionParser.new do |opts|    
      opts.on('-m', '--module STR', 'Load configuration/monitor module') do |m|
        options[:module] = m
      end
  
      opts.on('-t', '--target STR', 'Hostname or IP of target') do |h|
        options[:host] = h
      end
    
      opts.on('-p NUM', '--port NUM', 'TCP/UDP port number of target service (default 80)') do |p|
        options[:port] = p
      end
  
      opts.on('--ssl', 'Use SSL to connect to service') do
        options[:ssl] = true
      end
    
      opts.on('--soap', 'Assume request has XML payload') do
        options[:soap] = true
      end
  
      opts.on('-i', '--import FILE', 'Fuzz from requests in Burp XML format') do |i|
        options[:import] = i
      end
      
      opts.on('-u', '--upnp', 'Build list of fuzz requests from UPnP') do |i|
        options[:upnp] = true
        options[:soap] = true
        options[:fuzzers] = ['post']
      end
  
      opts.on('-f', '--fuzzers STR', 'Comma separated list of fuzzing engines to utilize (param,post,token,...)') do |f|
        options[:fuzzers] = f.split(',').map do |d|
          d.downcase.strip
        end
      end
      
      opts.on('-s', '--test-set STR', 'Comma separated list of test sets to utilize (buffer,integer,sqli,xxe,...)') do |s|
        options[:tests] = s.split(',').map do |d|
          d.downcase.strip
        end
      end
    
      opts.on('--delay NUM', 'Add a delay after each request') do |d|
        options[:delay] = d.to_f
      end
    
      opts.on('--skip-dedup', 'Skip proxy log de-duplication') do
        options[:skip_dedup] = true
      end
    
      opts.on('--reverse-log', 'Fuzz proxy log in reverse order') do
        options[:reverse_log] = true
      end
  
      opts.on('-v', '--verbose NUM', 'Enabled verbose output, from 0 (fail) to 4 (trace), default 2 (info)') do |v|
        options[:verbose] = v.to_i
      end
  
      opts.on( '-h', '--help', 'Display this screen' ) do
        puts opts
        exit
      end
    end

    optparse.parse!(cmd_line)
    options[:module] ||= 'generic' 
    options
  end
end
end