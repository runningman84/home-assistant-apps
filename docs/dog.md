# GuardDog

GuardDog app class.

Monitors a motion sensor and a door sensor and triggers a ringtone via
the Xiaomi/Aqara service when motion is detected while the alarm is
armed and the door sensor is in the expected state.

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