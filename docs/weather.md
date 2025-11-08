# WeatherWarning

Description
-----------
Monitors weather warning sensors and publishes alerts to Awtrix and optionally TTS, with rate limiting per warning.

Minimal apps.yaml snippet
-------------------------
```yaml
weather_warning:
  module: weather
  class: WeatherWarning
  current_warn_sensor: sensor.dwd_current
  future_warn_sensor: sensor.dwd_future
  awtrix_prefixes:
    - "awtrix/home"
```

Options
-------
- `current_warn_sensor`, `future_warn_sensor` (entities) — defaults: None
- `awtrix_prefixes` (list) — default: []

Notes
-----
The app reads warning attributes like `warning_count`, `warning_1_headline`, `warning_1_description`, etc.