# LightControl

Description
-----------
LightControl automates lights using motion sensors, illumination sensors and sun elevation. Supports night/evening scenes, guest and vacation modes, and can suppress automatic changes during alarm states.

Minimal apps.yaml snippet
-------------------------
```yaml
light_control:
  module: light
  class: LightControl
  lights:
    - light.hall
    - light.kitchen
  motion_sensors:
    - binary_sensor.motion_hall
    - binary_sensor.motion_kitchen
  night_scene: scene.night_lights
  min_illumination: 20
  motion_duration: 180
```

Notes
-----
- See `apps/light.py` for advanced options such as fluxer support and multiple illumination sensors.

Options
-------
Common (from `base.py`):

 - `motion_sensors` (list) — default: []
 - `device_trackers` (list) — default: []
 - `vacation_control`, `guest_control` (entities) — defaults: None

Light-specific:

 - `lights` (list) — default: []
 - `night_scene`, `on_scene`, `off_scene` (entity/scene) — defaults: None
 - `min_illumination` (int) — default: 25
 - `min_elevation` (int) — default: 10
 - `motion_duration` (int seconds) — default: 180