# GuardDog

GuardDog app: simple guard logic that reacts to motion and door sensors and triggers alarms/ringtones.

Main features:
- Watch a motion sensor and a door sensor and trigger a ringtone when motion is detected while alarm is armed.

Key configuration keys:
- motion_sensor: entity_id of motion sensor (required).
- door_sensor: entity_id of a door sensor (required).
- gw_mac: gateway MAC for Xiaomi Aqara ringtone service (required for the example service call).

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
dog:
  module: dog
  class: GuardDog
  # options:
  # door_sensor: <value>
  # gw_mac: <value>
  # motion_sensor: <value>
```

## Options

| key | default |
| --- | --- |
| `door_sensor` | `None` |
| `gw_mac` | `None` |
| `motion_sensor` | `None` |