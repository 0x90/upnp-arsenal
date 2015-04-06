class TelnetConfig < UFuzz::Config
  def options
    {
      platform:     'Embedded Firewall',
      username:     'admin',
      password:     '',
      admin_user:   'admin',
      admin_pass:   '',
      use_ssl:      false,
      use_session:  true,
      skip_urls:    /logincheck|logout/,
    }
  end
end