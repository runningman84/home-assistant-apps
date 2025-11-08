# FrigateControl

FrigateControl app: coordinate Frigate camera service with Home Assistant states and triggers.

Main features:
- Turn on/off Frigate camera recording/switches based on motion, openings, alarm and schedule.
- Provide grouped operations for cameras and switches and options to auto-enable/disable on certain events.

Key configuration keys:
- frigate_switches: list of switch entity ids to enable/disable Frigate recording or related integrations.
- frigate_cameras: list of camera entity ids to monitor/control.
- auto_turn_on_motion/opening/alarm: booleans to enable auto-start for corresponding events.

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
frigate:
  module: frigate
  class: FrigateControl
  # options:
  # auto_turn_off_alarm: True
  # auto_turn_off_motion: True
  # auto_turn_off_opening: True
  # auto_turn_on_alarm: True
  # auto_turn_on_motion: True
  # auto_turn_on_opening: True
  # frigate_cameras: []
  # frigate_switches: []
```

## Options

| key | default |
| --- | --- |
| `auto_turn_off_alarm` | `True` |
| `auto_turn_off_motion` | `True` |
| `auto_turn_off_opening` | `True` |
| `auto_turn_on_alarm` | `True` |
| `auto_turn_on_motion` | `True` |
| `auto_turn_on_opening` | `True` |
| `frigate_cameras` | `[]` |
| `frigate_switches` | `[]` |