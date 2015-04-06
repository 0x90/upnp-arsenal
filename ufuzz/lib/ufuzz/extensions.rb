class String
  def limit(len)
    if self.length > len
      self[0,len]
    else
      self
    end
  end
end