# GuardDog

Description
-----------
GuardDog plays a ringtone on a Xiaomi gateway when a configured motion sensor triggers while the alarm is armed. It's a small helper for audible alerts.

Minimal apps.yaml snippet
-------------------------
```yaml
guard_dog:
  module: dog
  class: GuardDog
  motion_sensor: binary_sensor.motion_backyard
  door_sensor: binary_sensor.door_back
  gw_mac: 'AA:BB:CC:DD:EE:FF'
```

Options
-------
- `motion_sensor` (entity) — required
- `door_sensor` (entity) — required
- `gw_mac` (str) — gateway MAC for Xiaomi ringtone call, required

Notes
-----
This app expects those keys to be present (it uses direct `self.args[...]` indexing).