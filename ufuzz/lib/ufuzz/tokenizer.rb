module UFuzz
class Tokenizer
  attr_accessor :tokens
  
  def initialize(str)
    @tokens = []
    @regex = /[@"\/\:=\[\]&,\r\n\|;\*\?\)\(\{\}\\ ]/
    
    prev = ''
    (0).upto(str.length-1) do |n|
      if str[n] =~ @regex
        @tokens << prev unless prev.empty?
        @tokens << str[n]
        prev = ''
      else
        prev += str[n]
      end
    end
    @tokens << prev if prev
    
    if @tokens =~ /(%[0-9a-f][0-9a-f])/i
      @tokens.map! { |t| t.split(/(%[0-9a-f][0-9a-f])/i) }
      @tokens.flatten!
    end

    @tokens
  end
  
  def fuzz_each_token(testcase, opts = {}, &block)    
    @tokens.each_with_index do |t,i|
      next if t =~ @regex || t =~ /%[0-9a-f][0-9a-f]/i #|| i < 20
      testcase.rewind(t)
      while(testcase.next?)
        f = testcase.next
        fuzz_positions(t, i, f, opts, &block)
      end
    end
  end
  
  def to_s
    @tokens.map { |t| t }.join('')
  end
  
  def fuzz_positions(tok, i, fuzz, opts)
    Config.instance.encoders.each do |encode|
      fuzz_val = encode.call(fuzz)
      ["#{fuzz_val}", "#{tok}#{fuzz_val}", "#{fuzz_val}#{tok}"].each do |f|
        t    = @tokens.dup
        t[i] = f
        yield Tokenizer.tok_to_string(t), i, fuzz
      end
    end
  end
  
  def self.tok_to_string(tok)
    tok.map { |t| t }.join('')
  end
end
end