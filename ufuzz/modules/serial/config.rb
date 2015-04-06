class SerialConfig < UFuzz::Config
  def options
    {
      platform:     'D-Link Router',
      use_ssl:      false,
      use_session:  false,
      #delay:        1,
      skip_urls: /AddPortMapping/ 
    }
  end
end