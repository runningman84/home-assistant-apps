# ClimateControl

Description
-----------
ClimateControl manages thermostats based on open windows/doors, presence, guest/vacation modes and environmental sensors (AQI, VOC, CO2). It can also react to motion and override temperatures for short periods.

Minimal apps.yaml snippet
-------------------------
```yaml
climate_control:
  module: climate
  class: ClimateControl
  climate_controls:
    - climate.living_room
  door_window_sensors:
    - binary_sensor.window_living
  home_temperature: 21
  away_temperature: 17
  vacation_temperature: 15
```

Notes
-----
- See `apps/climate.py` for advanced options like AQI thresholds, offsets and motion-based temperature control.

Options
-------
Common (from `base.py`):

 - `device_trackers` (list) — default: []
 - `vacation_control` (entity) — default: None
 - `guest_control` (entity) — default: None

Climate-specific:

 - `climate_controls` (list) — default: []
 - `external_temperature_sensor` (entity) — default: None
 - `aqi_sensor`, `voc_sensor`, `co2_sensor` (entities) — defaults: None
 - `home_temperature` (float) — default: 20
 - `away_temperature` (float) — default: 18
 - `vacation_temperature` (float) — default: 16
 - `motion_temperature` (float) — default: 21