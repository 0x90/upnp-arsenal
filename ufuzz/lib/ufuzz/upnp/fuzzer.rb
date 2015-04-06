require 'pp'

module UFuzz
module UPnP

class Fuzzer < UFuzz::Http::Fuzzer
  def run
    @upnp = Request.new
    @upnp.msearch(@config.msearch_timeout)
    @upnp.enumerate
    
    request_count = @upnp.generate_requests.count
    
    @upnp.generate_requests.each_with_index do |req, index|
      next if @config.skip_urls && req =~ @config.skip_urls
      host_header = req.match(/^Host: (.+)$/i)[1].strip
      host, port = host_header.split(':', 2)
      @config.host = host
      @config.port = port.to_i
      
      log "fuzzing host #{host_header} with request:\n#{req.gsub(/(\$PARAM_[0-9]+_\$)/, 'PARAM')}", INFO
      @request = UFuzz::Http::Request.new(req)
      soap_fuzzer
      
      @request = UFuzz::Http::Request.new(req.gsub(/(\$PARAM_[0-9]+_\$)/, '1'))
      if @config.fuzzers.include?('token') && index == (request_count-1)
        log "running token fuzzer on last request only", INFO
        token_fuzzer
      end
    end
  end
  
  def soap_fuzzer
    @request.to_s.scan(/(\$PARAM_[0-9]+_\$)/) do |params|
      params.each do |param_id|
        @testcase.rewind('')
        while(@testcase.next?)
          fuzz = @testcase.next
          @config.encoders.each do |encoder|
            encoded_fuzz = encoder.call(fuzz)
            temp_request = @request.to_s.gsub(param_id, encoded_fuzz).gsub(/(\$PARAM_[0-9]+_\$)/, '1')
            req = UFuzz::Http::Request.new(temp_request)
            req.update_content_length
            do_fuzz_case(req, 0, fuzz)
          end
        end
      end
    end
  end
end

end
end