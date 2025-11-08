# WasteReminder

Description
-----------
Notifies about upcoming waste collection using Awtrix and optional TTS. Driven by a calendar sensor that contains event message and start_time attributes.

Minimal apps.yaml snippet
-------------------------
```yaml
waste_reminder:
  module: waste
  class: WasteReminder
  waste_calender: sensor.waste_calendar
  awtrix_prefixes:
    - "awtrix/home"
```

Options
-------
- `waste_calender` (entity) — default: None
- `awtrix_prefixes` (list) — default: []

Notes
-----
The app looks for `start_time` and `message` attributes on the configured calendar sensor.