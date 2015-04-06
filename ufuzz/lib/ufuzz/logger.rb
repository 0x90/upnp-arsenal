require 'time'
require 'singleton'

CRASH = -1
FAIL = 0
WARN = 1
INFO = 2
DEBUG = 3
TRACE = 4

def log(message, level = INFO, opts = {})
  UFuzz::Logger.instance.log(message, level, opts)
end

module UFuzz
  
class Logger
  include Singleton
  
  def initialize
    @count  = 0
    @config = nil
    @log_level = 2
  end
  
  def lazy_init
    @config = Config.instance
    @log_level = @config.verbose
    
    @logdir ||= File.expand_path(File.dirname(__FILE__) + "/../../log")
    unless File.directory?(@logdir)
      Dir::mkdir(@logdir)
    end
    
    @directory ||= File.expand_path(@logdir + "/#{Process.ppid}#{Process.pid}_#{@config.module}-#{@config.app}_#{timestamp}")
    unless File.directory?(@directory)
      Dir::mkdir(@directory)
    end
  end
  
  def counter
    @count += 1
    @count = 1 if @@count > 9999
    "%04d" % @count
  end
  
  def timestamp
    @ts ||= Time.now.inspect.gsub(/ [\-+][0-9]+$/,'').gsub(/[ \/:\-_]/,'')
  end
  
  def filename
    @filename ||= @directory + "/fuzz.log"
  end
  
  def log_array(arr, level, opts={})
    arr.each do |msg|
      log(msg, level, opts)
    end
  end
  
  def log(message, level=INFO, opts={})
    if message.is_a? Array
      log_array(message, level, opts)
      return nil
    elsif message.is_a? Fault
      log_crash(message)
      return nil
    end
    
    if level <= @log_level
      ts = Time.now.iso8601
      case level
      when CRASH # for target crashes
        puts "[#{ts} EVENT DETECTED]".underline.colorize(:light_red) + " #{message}"
        log_to_file "[#{ts} EVENT] #{message}"
      when FAIL
        puts "[#{ts} FAIL]".colorize(:light_red) + " #{message}"
        log_to_file "[#{ts} FAIL] #{message}"
      when WARN
        puts "[#{ts} WARN]".colorize(:light_yellow) + " #{message}"
        log_to_file "[#{ts} WARN] #{message}"
      when INFO
        puts "[#{ts} INFO]".colorize(:light_white) + " #{message}"
        log_to_file "[#{ts} INFO] #{message}"
      when DEBUG
        puts "[#{ts} DEBUG]".colorize(:cyan) + " #{message}"
        #log_to_file "[#{ts} DEBUG] #{message}"
      when TRACE
        puts "[#{ts} TRACE]".colorize(:magenta) + " #{message}"
        #log_to_file "[#{ts} TRACE] #{message}"
      end
    end
  end
  
  def log_to_file(message)
    unless @config
      begin
        lazy_init
      rescue => e
        #puts e.message
        #puts e.backtrace
        return
      end
    end
    
    if @config.logging[:text]
      begin
        @logfile ||= File.open(filename, 'a')
      rescue Errno::ENOENT => e
        unless File.directory?(@directory)
          Dir::mkdir(@directory)
          retry
        end
        raise e
      end
      @logfile.puts message
      @logfile.flush
    end
  end
  
  def log_crash(fault)
    reason = fault.reason || 'unknown'
    crash_dir = @directory + "/" + "#{reason.downcase.gsub(/[\/ ]/, '_')}"
    unless File.directory?(crash_dir)
      Dir::mkdir(crash_dir)
    end
  
    File.open("#{crash_dir}/#{@config.req_summary.to_s.limit(40).downcase.gsub(/[\/ ]/, '_')}.log", 'a') do |f|
      f.puts "[#{Time.now.iso8601} EVENT DETECTED] *************************************" + "\n" +
                  '-' * 80 + "\n#{fault.tx}\n" + '-' * 80 + "\n#{fault.rx.to_s.limit(5000)}\n" + '-' * 80 +
                  "\n#{fault.crash_dump}\n\n"
    end
    log fault.pretty_print, CRASH
  end
  
  def close
    @logfile.close if @logfile
  end
end

end