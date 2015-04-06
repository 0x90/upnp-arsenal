$:.unshift(File.expand_path(File.dirname(__FILE__)))

require 'colorize'
require 'rbkb/extends'
require 'uri'
require 'ostruct'
require 'socket'
require 'ipaddr'
require 'net/http'
require 'thread'
require 'openssl'
require 'timeout'
require 'net/telnet'
require 'eventmachine'
require 'serialport'
require 'nokogiri'
require 'escape_utils'
require 'forwardable'
require 'active_support/inflector'

require 'ufuzz/extensions'
require 'ufuzz/fault'
require 'ufuzz/testcase/testcase'

# include all test case generators
Dir["#{File.expand_path(File.dirname(__FILE__))}/ufuzz/testcase/*.rb"].each {|file| require file }

require 'ufuzz/constants'
require 'ufuzz/errors'
require 'ufuzz/net/socket'
require 'ufuzz/net/ssl_socket'
require 'ufuzz/logger'
require 'ufuzz/validator'
require 'ufuzz/command_line'
require 'ufuzz/config'
require 'ufuzz/tokenizer'
require 'ufuzz/tag_splitter'
require 'ufuzz/monitor'
require 'ufuzz/fuzzer'

require 'ufuzz/http/request'
require 'ufuzz/http/response'
require 'ufuzz/http/cookies'
require 'ufuzz/http/connection'
require 'ufuzz/http/session'
require 'ufuzz/http/fuzzer'
require 'ufuzz/http/burp'

require 'ufuzz/upnp/request'
require 'ufuzz/upnp/fuzzer'

require 'ufuzz/helpers/telnet'
require 'ufuzz/helpers/syslog'

# include all modules
Dir["#{File.expand_path(File.dirname(__FILE__))}/../modules/*/*.rb"].each {|file| require file }

trap("INT") { puts ''; log "shutting down", WARN; exit }
