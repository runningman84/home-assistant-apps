# Apps reference

This document lists the included AppDaemon apps with a short description and the main configuration entry to use in `apps.yaml`.

- alarm.py — AlarmControl
  - Description: Automatic alarm system that arms/disarms based on device trackers and monitors sensors (doors, motion, water, fire). Supports notifications and camera snapshots.
  - Config key example: `alarm: class: AlarmControl`

- climate.py — ClimateControl
  - Description: Adjusts climate entities (thermostats) based on open windows/doors, presence (device trackers), guest/vacation modes and environmental sensors.
  - Config key example: `climate_control: class: ClimateControl`

- light.py / light_switch.py / hello.py — LightControl variants
  - Description: Motion- and condition-based lighting automation, night/evening scenes and manual switch handling.
  - Config key example: `light_control: class: LightControl`

- power.py — PowerControl
  - Description: Switches devices on/off based on motion, presence and schedules to save power.
  - Config key example: `power_control: class: PowerControl`

- camera.py — CameraImageScanner
  - Description: Runs image processing scans on configured image processors when sensors trigger.
  - Config key example: `camera_scanner: class: CameraImageScanner`

- telegram.py — TelegramBotEventListener
  - Description: Helper app to integrate Telegram commands and callbacks (alarm control, pictures, notifications).
  - Config key example: `telegram_bot: class: TelegramBotEventListener`

Other small apps (see source for details): `awake/awtrix.py`, `cleanup.py`, `dog.py`, `frigate.py`, `heat.py`, `temperature_sync.py`, `weather.py`, `waste.py`.

For full configuration examples, refer to `sample_config/apps.yaml`.
# App descriptions

Short descriptions of the AppDaemon apps included in this repository.

 - `base.py` — BaseApp: common helper functions used by many apps (logging, counting sensors, notification helpers, time/workday utilities, state-change recording, and other shared utilities).

 - `hello.py` — HelloWorld: trivial example app that logs on initialization. Useful as a minimal template.

 - `light.py` — LightControl: automatic light control based on motion, illumination, sun elevation, presence, vacation/guest modes and alarm state. Supports scenes, delayed reactions and internal/external change suppression.

 - `light_switch.py` — LightSwitch: handles remote control events (brightness up/down, arrow clicks/holds, toggles) and maps them to light entities. Designed for physical remote/button integrations.

 - `power.py` — PowerControl: controls power outlets / switches similar to LightControl but focused on power devices. Turns devices on/off based on motion, presence, vacation, night and media playback.

 - `climate.py` — ClimateControl: manages climate entities (thermostats / ACs). Chooses temperature, HVAC mode, fan/preset modes based on presence, open windows, external/outside temperature, air quality (AQI/VOC/CO2), seasonal thresholds and guest/vacation modes.

 - `temperature_sync.py` — TemperatureSync: copies a single input temperature sensor to one or more numeric outputs (useful to synchronize temperature sensors or setpoints across entities).

 - `alarm.py` — AlarmControl: a comprehensive alarm management app. Listens to binary sensors (doors, windows, motion, environmental) and device trackers, evaluates arming/disarming rules, auto-arming schedules, generates notifications (media, Telegram, awtrix), and triggers sirens/alarms when thresholds are exceeded.

 - `camera.py` — CameraImageScanner: starts/stops image processing scans for an image_processing entity based on configured sensors.

 - `frigate.py` — FrigateControl: coordinates Frigate camera recording/streaming and related switches. Can auto-enable cameras/switches for motion/openings/alarm states and turn them off otherwise.

 - `awtrix.py` — AwtrixControl: publishes MQTT commands to Awtrix displays based on motion, presence, alarm state and timers (power, sleep, custom payloads).

 - `cleanup.py` — Cleanup: small utility that triggers a cleanup service when a sensor reports too many files or total bytes above configured limits.

 - `dog.py` — GuardDog: simple guard that plays a ringtone on a Xiaomi gateway when a motion sensor triggers while the alarm is armed.

 - `telegram.py` — TelegramBotEventListener: listens for Telegram commands and callbacks to provide alarm status, arm/disarm controls and send notifications to configured users.

 - `waste.py` — WasteReminder: notifies about upcoming waste collection using awtrix and TTS (once per day/tomorrow limits), driven by a calendar sensor.

 - `weather.py` — WeatherWarning: monitors weather warning sensors and publishes alerts to awtrix and optionally TTS, with rate limiting per-warning.

If you want these descriptions added to `README.md` instead, or expanded with configuration examples for each app (args and typical yaml snippets), tell me which apps to document in more detail and I will add sample configuration blocks.
