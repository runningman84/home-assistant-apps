# WasteReminder

WasteReminder app: notify occupants about upcoming waste collection events.

Main features:
- Read a calendar-style sensor for upcoming waste collection and notify via AWTRIX/TTS when collection is today/tomorrow.
- Throttles TTS messages to avoid repeated announcements and respects night windows.

Key configuration keys:
- waste_calendar: entity id of a calendar or sensor that exposes 'start_time' and 'message' attributes.
- awtrix_prefixes: optional list of AWTRIX prefixes to notify via MQTT.

Example:
```yaml
waste_reminder:
    module: waste
    class: WasteReminder
    waste_calendar: sensor.waste_calendar
    awtrix_prefixes:
        - "awtrix/home"
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
waste:
  module: waste
  class: WasteReminder
  # options:
  # awtrix_prefixes: []
  # waste_calendar: <value>
```

## Options

| key | default |
| --- | --- |
| `awtrix_prefixes` | `[]` |
| `waste_calendar` | `None` |