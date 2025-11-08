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