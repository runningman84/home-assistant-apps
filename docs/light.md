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