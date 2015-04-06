module UFuzz
  
class TagSplitter
  attr_accessor :tokens
  
  def initialize(str)
    @tokens = []
    @regex = />.*?</
    @tokens = str.split(@regex).map { |m| m }.zip(str.scan(@regex).map { |m| m }).flatten.compact
  end
  
  def fuzz_each_token(testcase, &block)
    @tokens.each_with_index do |t,i|
      next unless t =~ @regex
      testcase.rewind(t)
      while(testcase.next?)
        f = testcase.next
        fuzz_positions(t, i, f, &block)
      end
    end
  end
  
  def to_s
    @tokens.map { |t| t }.join('')
  end
  
  def fuzz_positions(tok, i, fuzz)
    [">#{fuzz}<"].each do |f|
      t = @tokens.dup
      t[i] = f
      yield Tokenizer.tok_to_string(t), i, fuzz
    end
  end
  
  def self.tok_to_string(tok)
    tok.map { |t| t }.join('')
  end
end

end
