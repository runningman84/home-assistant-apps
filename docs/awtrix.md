# AwtrixControl

AwtrixControl app: send notifications and power commands to AWTRIX devices via MQTT.

Main features:
- Publish power/sleep/notification payloads to configured AWTRIX MQTT prefixes.
- React to motion, device tracker and alarm events to power on/off or display messages.

Key configuration keys:
- awtrix_prefixes: list of MQTT topic prefixes for your AWTRIX devices (required).

Example:
```yaml
awtrix:
    module: awtrix
    class: AwtrixControl
    awtrix_prefixes:
        - "awtrix/device1"
        - "awtrix/device2"
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
awtrix:
  module: awtrix
  class: AwtrixControl
  # options:
  # awtrix_prefixes: []
```

## Options

| key | default |
| --- | --- |
| `awtrix_prefixes` | `[]` |