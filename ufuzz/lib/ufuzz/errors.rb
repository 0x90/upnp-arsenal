module UFuzz
  module Errors
    class Error < StandardError; end

    class SocketError < Error
      attr_reader :socket_error

      def initialize(socket_error=nil)
        if socket_error.message =~ /certificate verify failed/
          super("Unable to verify certificate")
        else
          super("#{socket_error.message} (#{socket_error.class})")
        end
        set_backtrace(socket_error.backtrace)
        @socket_error = socket_error
      end
    end

    class Timeout < Error; end
  end
end