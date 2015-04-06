module UFuzz
  HTTP_1_1 = " HTTP/1.1\r\n"
  CR_NL = "\r\n"

  DEFAULT_NONBLOCK = OpenSSL::SSL::SSLSocket.public_method_defined?(:connect_nonblock) &&
      OpenSSL::SSL::SSLSocket.public_method_defined?(:read_nonblock) &&
      OpenSSL::SSL::SSLSocket.public_method_defined?(:write_nonblock)
  
  NO_ENTITY = [204, 205, 304].freeze
  
  HTTP_ERRORS = {
    100 => 'Continue',
    101 => 'Switching Protocols',
    200 => 'OK',
    201 => 'Created',
    202 => 'Accepted',
    203 => 'Non-Authoritative Information',
    204 => 'No Content',
    205 => 'Reset Content',
    206 => 'Partial Content',
    300 => 'Multiple Choices',
    301 => 'Moved Permanently',
    302 => 'Found',
    303 => 'See Other',
    304 => 'Not Modified',
    305 => 'Use Proxy',
    307 => 'Temporary Redirect',
    400 => 'Bad Request',
    401 => 'Unauthorized',
    402 => 'Payment Required',
    403 => 'Forbidden',
    404 => 'Not Found',
    405 => 'Method Not Allowed',
    406 => 'Not Acceptable',
    407 => 'Proxy Authentication Required',
    408 => 'Request Timeout',
    409 => 'Conflict',
    410 => 'Gone',
    411 => 'Length Required',
    412 => 'Precondition Failed',
    413 => 'Request Entity Too Large',
    414 => 'Request-URI Too Long',
    415 => 'Unsupported Media Type',
    416 => 'Request Range Not Satisfiable',
    417 => 'Expectation Failed',
    422 => 'Unprocessable Entity',
    500 => 'InternalServerError',
    501 => 'Not Implemented',
    502 => 'Bad Gateway',
    503 => 'Service Unavailable',
    504 => 'Gateway Timeout'
  }
  
  unless ::IO.const_defined?(:WaitReadable)
    class ::IO
      module WaitReadable; end
    end
  end

  unless ::IO.const_defined?(:WaitWritable)
    class ::IO
      module WaitWritable; end
    end
  end
end