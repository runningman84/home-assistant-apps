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