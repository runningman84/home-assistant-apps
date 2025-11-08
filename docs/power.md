# PowerControl

Description
-----------
PowerControl toggles power outlets and switches based on motion, presence and schedules. It helps reduce standby power use by turning off unused devices.

Minimal apps.yaml snippet
-------------------------
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

Notes
-----
- See `apps/power.py` for options like standby sensors and night_force_off.

Options
-------
Common (from `base.py`):

 - `motion_sensors`, `device_trackers` (lists) — defaults: []
 - `vacation_control`, `guest_control` (entities) — defaults: None

Power-specific:

 - `power_controls` (list) — default: []
 - `standby_sensors` (list) — default: []
 - `night_force_off` (bool) — default: True
 - `tracker_duration`, `motion_duration` (seconds) — defaults: see `base.py`