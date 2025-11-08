# AlarmControl

AlarmControl app: manage sensors, arming/disarming, sirens and notifications for the alarm system.

Main features:
- Handle arming/disarming (manual, schedules, device-tracker based auto-arm).
- Map and categorize sensors (door, window, motion, tamper, environmental) into alarm types.
- Trigger notifications via configured notify services (TTS, telegram, awtrix, scripts).
- Integrate camera references for snapshots or event context.
- Support thresholds for fire/water and automatic reactions.

Key configuration keys (most optional with sensible defaults):
- alarm_control_panel: entity_id of the alarm_control_panel to monitor/control.
- device_trackers: list of device_tracker entity ids used for auto-arm/disarm.
- armed_home_binary_sensors, armed_away_binary_sensors, armed_night_binary_sensors: lists of sensor ids used per arming mode.
- notify_service: service to call for notifications (e.g., script.notify_all).
- cameras: optional list of camera entity ids to include in alerts.
- fire_temperature_threshold: numeric threshold for fire temperature sensor.

Example `apps.yaml` snippet :

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

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
alarm:
  module: alarm
  class: AlarmControl
  # options:
  # alarm_arm_night_after_time: 23:15:00
  # alarm_arm_night_before_time: 06:00:00
  # alarm_control_buttons: []
  # alarm_lights: []
  # alarm_pin: <value>
  # armed_away_binary_sensors: []
  # armed_away_image_processing_sensors: []
  # armed_home_binary_sensors: []
  # armed_home_image_processing_sensors: []
  # burglar_siren_switches: []
  # fire_binary_sensors: []
  # fire_siren_switches: []
  # fire_temperature_sensors: []
  # fire_temperature_threshold: 50
  # language: english
  # water_binary_sensors: []
```

## Options

| key | default |
| --- | --- |
| `alarm_arm_night_after_time` | `23:15:00` |
| `alarm_arm_night_before_time` | `06:00:00` |
| `alarm_control_buttons` | `[]` |
| `alarm_lights` | `[]` |
| `alarm_pin` | `None` |
| `armed_away_binary_sensors` | `[]` |
| `armed_away_image_processing_sensors` | `[]` |
| `armed_home_binary_sensors` | `[]` |
| `armed_home_image_processing_sensors` | `[]` |
| `burglar_siren_switches` | `[]` |
| `fire_binary_sensors` | `[]` |
| `fire_siren_switches` | `[]` |
| `fire_temperature_sensors` | `[]` |
| `fire_temperature_threshold` | `50` |
| `language` | `english` |
| `water_binary_sensors` | `[]` |