# AwtrixControl

Description
-----------
AwtrixControl publishes MQTT commands to Awtrix displays based on motion, presence and alarm states. It uses configured MQTT topic prefixes to address devices.

Minimal apps.yaml snippet
-------------------------
```yaml
awtrix:
  module: awtrix
  class: AwtrixControl
  awtrix_prefixes:
    - "awtrix/device1"
    - "awtrix/device2"
```

Options
-------
- `awtrix_prefixes` (list) — default: []
- Common `BaseApp` options apply (motion_sensors, device_trackers, alarm_control_panel, etc.)

Notes
-----
This app sends MQTT payloads under each configured prefix (e.g. `PREFIX/power`, `PREFIX/sleep`).