module UFuzz
module Http

class Burp
  attr_accessor :doc, :entries, :config
  
  def initialize(config)
    @config = config
    
    load_doc config.import
    process_doc
  end
  
  def load_doc(xml_file)
    @doc = Nokogiri::XML(File.read xml_file)
  end
  
  def process_doc
    @entries = []
    doc.root.xpath('/items/item').each do |i|
      entry = []
      entry << i.xpath('request').children.first.content.d64
      entry << (i.xpath('response').children.first.content.d64 rescue '')
      @entries << entry
    end
    
    @entries.reverse! if @config.reverse_log
    log "processing the following requests:", INFO
    @entries.each do |e|
      log Request.new(e[0]).first_line, INFO
    end
  end      
  
  def each_entry
    if block_given?
      @entries.each do |e|
        yield(e[0], e[1])
      end
    else
      raise SyntaxError
    end
  end
end

end
end
