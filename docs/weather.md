# WeatherWarning

WeatherWarning app: announce or notify about weather warnings based on configured sensors.

Main features:
- Monitor current and future weather-warning sensors and announce warnings via AWTRIX/TTS.
- Track per-warning TTS counters to avoid repeated vocal alerts and respect night windows.

Key configuration keys:
- current_warn_sensor, future_warn_sensor: sensors exposing warning_count and per-warning attributes (name, headline, description, start, end).
- awtrix_prefixes: optional list of AWTRIX MQTT prefixes to publish notifications to.

Example:
```yaml
weather_warning:
    module: weather
    class: WeatherWarning
    current_warn_sensor: sensor.dwd_current
    future_warn_sensor: sensor.dwd_future
    awtrix_prefixes:
        - "awtrix/home"
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
weather:
  module: weather
  class: WeatherWarning
  # options:
  # awtrix_prefixes: []
  # current_warn_sensor: <value>
  # future_warn_sensor: <value>
```

## Options

| key | default |
| --- | --- |
| `awtrix_prefixes` | `[]` |
| `current_warn_sensor` | `None` |
| `future_warn_sensor` | `None` |