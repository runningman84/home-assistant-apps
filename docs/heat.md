# HeatSaver

Description
-----------
HeatSaver (and similar heat-related helpers) manage climate devices to avoid overheating, stop heating when windows open or nobody is home, and apply guest/vacation profiles.

Minimal apps.yaml snippet
-------------------------
```yaml
heat_saver:
  module: heat
  class: HeatSaver
  climate_controls:
    - climate.floor_heating
  door_window_sensors:
    - binary_sensor.window_kitchen
  home_temperature: 20
```

Options
-------
- `door_window_sensors` (list) — default: []
- `device_trackers`, `motion_sensors`, `climate_controls` — defaults: []
- `vacation_control`, `guest_control` — defaults: None
- `wait_duration` (seconds) — default: 15
- Many climate-related options mirror `climate.py` (home/away/vacation/open temperatures, hvac modes, thresholds)
