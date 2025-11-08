# FrigateControl

Description
-----------
FrigateControl coordinates Frigate cameras and related switches. It can auto-enable cameras/switches on motion/openings/alarm states and turn them off otherwise.

Minimal apps.yaml snippet
-------------------------
```yaml
frigate_control:
  module: frigate
  class: FrigateControl
  frigate_cameras:
    - camera.front_yard
  frigate_switches:
    - switch.frigate_power
  auto_turn_on_motion: true
```

Options
-------
- `frigate_cameras` (list) — default: []
- `frigate_switches` (list) — default: []
- `auto_turn_on_motion`, `auto_turn_on_opening`, `auto_turn_on_alarm` (bool) — defaults: True
- `auto_turn_off_motion`, `auto_turn_off_opening`, `auto_turn_off_alarm` (bool) — defaults: True
- Common `BaseApp` options apply (motion/opening sensors, alarm_control_panel)
