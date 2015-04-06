module UFuzz
module Http

class Fuzzer < UFuzz::Fuzzer
  def run
    log "begin #{self.class}", INFO
    start_time = Time.now.to_f
    @count = 0
    
    if config.request
      @request = Request.new(@config.request)
      @config.req_summary = @request.verb_path
      log "fuzzing request #{@request.summary}", INFO
      
      (config.fuzzers || default_fuzzers).each do |f|
        new_session
        begin
          self.send("#{f}_fuzzer".to_sym)
        rescue
          log "error running #{f}_fuzzer", FAIL
          log e.message, DEBUG
          log e.backtrace, TRACE
        end
      end

    elsif config.import
      @transactions = UFuzz::Http::Burp.new(config)
      @transactions.each_entry do |req, resp|
        @request  = Request.new(req)
        @config.req_summary = @request.verb_path
        @response = resp
        
        if config.skip_urls && @request.summary =~ config.skip_urls
          log "skipping request #{@request.summary}", INFO
          next
        else
          log "fuzzing request #{@request.summary}", INFO
        end
        
        (config.fuzzers || default_fuzzers).each do |f|
          new_session
          begin
            self.send("#{f}_fuzzer".to_sym)
          rescue => e
            log "error running #{f}_fuzzer", FAIL
            log e.message, DEBUG
            log e.backtrace, TRACE
          end
        end
      end
    end
    
    log "finished #{self.class}, #{(@count / (Time.now.to_f - start_time)).to_i} req/sec, #{@count} total", INFO
    cleanup
  end
  
  def default_fuzzers
    ['param', 'post', 'header', 'rest', 'verb']
  end
  
  def new_session
    10.times do
      if @config.use_session && !@session.valid?
        @session.clear
        @session.create
        @request.update_cookies(@session)
      else
        return @session
      end
      sleep(1)
    end
    raise "new_session: could not establish new session"
  end
  
  def header_fuzzer
    headers = @config.fuzzable_headers.merge(@request.headers)
    headers = headers.merge({ 'User-Agent' => 'Mozilla/5.0' }) # speed fix
    
    @config.fuzzable_headers.each_key do |header|
      value = headers[header]
      t = Tokenizer.new(value)
      t.fuzz_each_token(testcase) do |fuzz_header, i, fuzz|
        req = Request.new(@request.to_s)
        req.set_header(header, fuzz_header)
        do_fuzz_case(req, i, fuzz)
      end
    end

    testcase.rewind
    while(testcase.next?)
      req = Request.new(@request.to_s)
      fuzz = testcase.next
      req.set_header(fuzz.to_s, '1')
      do_fuzz_case(req, req.to_s.index(fuzz.to_s), fuzz)
    end
  end
  
  def param_fuzzer
    @request.url_variables.each_pair do |k,v|
      t = Tokenizer.new(v)
      t.fuzz_each_token(testcase) do |fuzz_param, i, fuzz|
        req = Request.new(@request.to_s)
        req.query_string = @request.url_variables.merge({k => fuzz_param})
        do_fuzz_case(req, i, fuzz)
      end
    end
    
    @request.url_variables.each_pair do |k,v|
      testcase.rewind
      while(testcase.next?)
        fuzz = testcase.next
        @config.encoders.each do |encoder|
          encoded_fuzz = encoder.call(fuzz)
          req = Request.new(@request.to_s)
          req.query_string = @request.url_variables.merge({k => encoded_fuzz})
          do_fuzz_case(req, req.first_line.index(encoded_fuzz), fuzz)
        end
      end
    end
    
    if @config.extra_param
      @config.extra_param.each_pair do |k,v|
        t = Tokenizer.new(v)
        t.fuzz_each_token(testcase) do |fuzz_param, i, fuzz|
          req = Request.new(@request.to_s)
          req.query_string = @request.url_variables.merge({k => fuzz_param})
          do_fuzz_case(req, i, fuzz)
        end
      end
    end
    
    testcase.rewind
    while(testcase.next?)
      fuzz = testcase.next
      @config.encoders.each do |encoder|
        encoded_fuzz = encoder.call(fuzz)
        req = Request.new(@request.to_s)
        req.query_string = @request.url_variables.merge({encoded_fuzz => '1'})
        do_fuzz_case(req, req.first_line.index(encoded_fuzz), fuzz)
      end
    end
  end
  
  def post_fuzzer
    if @request.post?
      if @config.soap
        t = Tokenizer.new(@request.body)
        t.fuzz_each_token(testcase) do |fuzz_var, i, fuzz|
          req = Request.new(@request.to_s)
          req.body = fuzz_var
          do_fuzz_case(req, i, fuzz)
        end
      else
        @request.body_variables.each_pair do |k,v|
          next if @config.csrf_token_regex && k =~ @config.csrf_token_regex
          t = Tokenizer.new(v)
          t.fuzz_each_token(testcase) do |fuzz_var, i, fuzz|
            req = Request.new(@request.to_s)
            req.body = req.body_variables.merge({k => fuzz_var})
            do_fuzz_case(req, i, fuzz)
          end
        end
      
        @request.body_variables.each_pair do |k,v|
          testcase.rewind
          while(testcase.next?)
            fuzz = testcase.next
            @config.encoders.each do |encoder|
              encoded_fuzz = encoder.call(fuzz)
              req = Request.new(@request.to_s)
              req.body = @request.body_variables.merge({k => encoded_fuzz})
              do_fuzz_case(req, req.first_line.index(encoded_fuzz), fuzz)
            end
          end
        end
      
        testcase.rewind
        while(testcase.next?)
          fuzz = testcase.next
          @config.encoders.each do |encoder|
            encoded_fuzz = encoder.call(fuzz)
            req = Request.new(@request.to_s)
            req.body = req.body_variables.merge({encoded_fuzz => '1'})
            do_fuzz_case(req, req.body.index(encoded_fuzz), fuzz)
          end
        end
      end
    end
  end
  
  def rest_fuzzer
    t = Tokenizer.new(@request.path)
    t.fuzz_each_token(testcase) do |fuzz_path, i, fuzz|
      req = Request.new(@request.to_s)
      req.path = fuzz_path
      do_fuzz_case(req, i, fuzz)
    end
  end
  
  def token_fuzzer
    t = Tokenizer.new(request.to_s)
    t.fuzz_each_token(testcase) do |r, i, f|
      do_fuzz_case(Request.new(r).update_content_length, i, f)
    end
  end
  
  def verb_fuzzer
    testcase.rewind(@request.verb)
    while testcase.next?
      req  = Request.new(@request.to_s)
      fuzz = testcase.next
      req.verb = fuzz.to_s
      do_fuzz_case(req, req.first_line.index(fuzz.to_s), fuzz)
    end
  end
end

end
end