class GenericConfig < UFuzz::Config
  def options
    {
      platform:     'Generic',
      use_ssl:      false,
      use_session:  false,
      encoders:     [ proc { |f| f.to_s } ],
      #skip_urls:   /firmwareupdate1|UpdateWeeklyCalendar|ChangeFriendlyName/,
      #delay:       1, 
    }
  end
end