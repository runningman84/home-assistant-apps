# BaseApp

Base utilities for AppDaemon apps providing common helpers and configuration defaults.

This module provides a `BaseApp` class that other app modules inherit from. It
centralizes common configuration keys, sensible defaults, and utility helpers used
across multiple apps (e.g., motion/opening counters, night window helpers, TTS/awtrix helpers).

Common args provided by `BaseApp` (all optional unless noted):
- opening_sensors, motion_sensors, illumination_sensors, device_trackers
- vacation_control, guest_control, alarm_control_panel
- night_start, night_end, night_start_workday, night_end_workday
- notify_service, awtrix_prefixes, tts_devices
- external_change_timeout, internal_change_timeout

See module docstrings and inline examples for canonical usage and common options used across apps.

## Minimal apps.yaml snippet

```yaml
base:
  module: base
  class: BaseApp
  # options:
  # alarm_control_panel: <value>
  # alexa_media_devices: []
  # alexa_monkeys: []
  # awake_sensors: []
  # awake_timeout: <complex>
  # awtrix_prefixes: []
  # device_trackers: []
  # external_change_timeout: <complex>
  # guest_control: <value>
  # holiday_sensor: <value>
  # illumination_sensors: []
  # internal_change_timeout: 10
  # language: english
  # lights: []
  # media_players: []
  # motion_sensors: []
  # motion_timeout: <complex>
  # night_end: 08:30:00
  # night_end_workday: 06:30:00
  # night_start: 23:15:00
  # night_start_workday: 22:15:00
  # notify_service: <value>
  # notify_targets: []
  # notify_title: AlarmSystem triggered, possible {}
  # opening_sensors: []
  # opening_timeout: 30
  # silent_control: <value>
  # telegram_user_ids: []
  # tracker_timeout: 60
  # tts_devices: []
  # vacation_control: <value>
  # vacation_timeout: 60
  # vacuum_cleaners: []
  # workday_sensor: <value>
  # workday_tomorrow_sensor: <value>
```

## Options

| key | default |
| --- | --- |
| `alarm_control_panel` | `None` |
| `alexa_media_devices` | `[]` |
| `alexa_monkeys` | `[]` |
| `awake_sensors` | `[]` |
| `awake_timeout` | `<complex>` |
| `awtrix_prefixes` | `[]` |
| `device_trackers` | `[]` |
| `external_change_timeout` | `<complex>` |
| `guest_control` | `None` |
| `holiday_sensor` | `None` |
| `illumination_sensors` | `[]` |
| `internal_change_timeout` | `10` |
| `language` | `english` |
| `lights` | `[]` |
| `media_players` | `[]` |
| `motion_sensors` | `[]` |
| `motion_timeout` | `<complex>` |
| `night_end` | `08:30:00` |
| `night_end_workday` | `06:30:00` |
| `night_start` | `23:15:00` |
| `night_start_workday` | `22:15:00` |
| `notify_service` | `None` |
| `notify_targets` | `[]` |
| `notify_title` | `AlarmSystem triggered, possible {}` |
| `opening_sensors` | `[]` |
| `opening_timeout` | `30` |
| `silent_control` | `None` |
| `telegram_user_ids` | `[]` |
| `tracker_timeout` | `60` |
| `tts_devices` | `[]` |
| `vacation_control` | `None` |
| `vacation_timeout` | `60` |
| `vacuum_cleaners` | `[]` |
| `workday_sensor` | `None` |
| `workday_tomorrow_sensor` | `None` |