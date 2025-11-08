# PowerControl

PowerControl app: manage power outlets and devices based on motion, presence and schedules.

Main features:
- Automatically switch power controls on/off based on motion, presence, media playback and schedules.
- Respect vacation and alarm states to avoid turning devices on when not desired.
- Track and count switches and provide simple group operations.

Key configuration keys:
- power_controls: list of switch entity ids to control (required).
- motion_sensors, device_trackers: optional lists to decide when to turn devices on/off.
- tracker_duration: how long after last device_tracker presence to consider someone present.
- night_start: time to perform nightly power actions (configure via BaseApp defaults).

Example:
```yaml
power_control:
    module: power
    class: PowerControl
    power_controls:
        - switch.tv_living_room
        - switch.receiver
    motion_sensors:
        - binary_sensor.motion_living
    tracker_duration: 60
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
power:
  module: power
  class: PowerControl
  # options:
  # night_force_off: True
  # power_controls: []
  # standby_power_limit: 0
  # standby_sensors: []
```

## Options

| key | default |
| --- | --- |
| `night_force_off` | `True` |
| `power_controls` | `[]` |
| `standby_power_limit` | `0` |
| `standby_sensors` | `[]` |