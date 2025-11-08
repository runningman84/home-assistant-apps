# AlarmControl

Description
-----------
AlarmControl automatically arms/disarms and monitors sensors (doors, motion, water, fire). It supports notifications, camera snapshots and multiple arming modes (home/away/night/vacation).

Minimal apps.yaml snippet
-------------------------
```yaml
alarm:
  module: alarm
  class: AlarmControl
  alarm_control_panel: alarm_control_panel.ha_alarm
  device_trackers:
    - device_tracker.phone_anna
    - device_tracker.phone_bob
  armed_away_binary_sensors:
    - binary_sensor.front_door
    - binary_sensor.back_door
  notify_service: script.notify_all
  cameras:
    - camera.front_door
```

Notes
-----
- See `apps/alarm.py` for the full list of options and defaults.
- Use `APPS.md` or `README.md` for pointers to other helpers (Telegram, Awtrix).

Options
-------
Common (from `base.py`):

 - `opening_sensors` (list) — default: []
 - `motion_sensors` (list) — default: []
 - `device_trackers` (list) — default: []
 - `vacation_control` (entity) — default: None
 - `guest_control` (entity) — default: None
 - `notify_service` (service/entity) — default: None

Alarm-specific:

 - `armed_home_binary_sensors` (list) — default: []
 - `armed_away_binary_sensors` (list) — default: []
 - `armed_home_image_processing_sensors` (list) — default: []
 - `armed_away_image_processing_sensors` (list) — default: []
 - `water_binary_sensors` (list) — default: []
 - `fire_binary_sensors` (list) — default: []
 - `alarm_control_buttons` (list) — default: []
 - `alarm_lights` (list) — default: []
 - `camera_snapshot_path` (str) — default: `/tmp`
 - `camera_snapshot_regex` (str) — default: `camera_.*\d+_\d+\.jpg`