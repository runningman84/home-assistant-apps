# WelcomeControl

WelcomeControl app: announce residents and react to door/motion sensors.

Main features implemented by this module:
- Listen for the configured `door_sensor` opening event and, when it
    occurs, determine whether people are arriving ("coming") or leaving
    ("going") based on inside/outside motion sensors.
- If somebody is coming and device trackers show known people arrived
    recently, schedule a short-delayed media notification welcoming them.

Key configuration keys used by the app:
- `resident_timeout`: seconds within which a device_tracker's "home"
    state is considered a recent arrival (default: 300).
- `door_sensor`: entity id of the door binary sensor to listen for.
- `inside_motion_sensor`, `outside_motion_sensor`: motion sensors used
    to decide arrival direction.
- `device_trackers`: a list of device_tracker entity ids (provided by the
    BaseApp or app config) that are used by `get_residents()`.

Notes:
- This app does not publish MQTT payloads itself; it delegates to
    existing media/notify helpers via `notify_media` and schedules them
    using `run_in` for a short delay.

## Minimal apps.yaml snippet

```yaml
welcome:
  module: welcome
  class: WelcomeControl
  # options:
  # cooldown_timeout: 60
  # door_sensor: <value>
  # inside_motion_sensor: <value>
  # language: german
  # name_mapping: {}
  # outside_motion_sensor: <value>
  # resident_timeout: 300
```

## Options

| key | default |
| --- | --- |
| `cooldown_timeout` | `60` |
| `door_sensor` | `None` |
| `inside_motion_sensor` | `None` |
| `language` | `german` |
| `name_mapping` | `{}` |
| `outside_motion_sensor` | `None` |
| `resident_timeout` | `300` |