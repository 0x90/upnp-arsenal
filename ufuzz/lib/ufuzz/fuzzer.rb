module UFuzz

class Fuzzer
  attr_accessor :testcase, :config, :request, :mutex, :connection, :session
  
  def initialize(config)
    @config     = config
    @connection = config.create_connection
    @testcase   = config.create_testcase
    @request    = config.create_request
    @session    = config.create_session
    @monitor    = @config.create_monitor
    @count      = 0
    @config.req_summary = @config.req_summary || 'default'
  end
  
  def new_session
  end
  
  def parser
    if @request.is_a?(Array)
      @request.each do |req|
        standard_fuzz(req)
      end
    else
      standard_fuzz(req)
    end
  end
  
  def standard_fuzz(req)
    t = Tokenizer.new(req.dup)
    t.fuzz_each_token(@testcase) do |fuzz_case, i, fuzz|
      do_fuzz_case(fuzz_case, i, fuzz)
    end
  end
  
  def do_fuzz(req, position, fuzz, opts)
    @count += 1
    conn = nil
    resp = nil
    
    Timeout::timeout(15) do
      log "tx >>>\n#{req}", TRACE
      conn = config.create_connection
      resp = conn.send(req)
      if resp.respond_to?(:summary)
        log "rx <<< #{resp.summary}", TRACE
      else
        log "rx <<< #{resp}", TRACE
      end
    end
    
    check_fault(fuzz, req, resp)

    sleep @config.delay if @config.delay
    
  rescue Timeout::Error
    if conn.connection_success?
      check_fault(fuzz, req)
    else
      log "connect fail", WARN
    end
  end
  
  def do_fuzz_case(req, position, fuzz, opts = {})
    #if fuzz.threadable?
    #  if Thread.list.count >= @config.thread_count
    #    Thread.list[1].join
    #  end
    #  Thread.new { do_fuzz(req, position, fuzz, opts) }
    #else
      do_fuzz(req, position, fuzz, opts)
    #end
  end
  
  def check_fault(fuzz, req, resp = nil)
    fault = fuzz.test(resp)
  
    if fault
      fault.tx = req
      fault.rx = resp
      log fault
      new_session
    end
  end
  
  def run
    log "begin #{self.class}", INFO
    start_time = Time.now.to_f
    @count = 0
    
    parser
    
    log "finished #{self.class}, #{(@count / (Time.now.to_f - start_time)).to_i} req/sec, #{@count} total", INFO
    cleanup
  end
  
  def cleanup
    @session.clear if @config.use_session
  end
  
  def start!
    run
  end
  
  # class methods
  
  def self.load(opts)
    config = UFuzz::Config.create(opts)
    
    if config.upnp
      fuzzer = UFuzz::UPnP::Fuzzer.new(config)
    else
      fuzzer = UFuzz::Http::Fuzzer.new(config)
    end
    
    fuzzer
  end
end

end