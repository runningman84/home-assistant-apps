# LightControl

LightControl app: automatically control lights based on motion, trackers, illumination and schedules.

Main features:
- Automatically turn lights on/off based on motion sensors, illumination sensors, sun elevation and presence.
- Support scenes for night/on/off transitions and optional fluxer/pattern control.
- Respect vacation, guest, and alarm states to avoid unintended changes.
- Configurable auto_turn_on / auto_turn_off toggles and thresholds for illumination/elevation.

Key configuration keys:
- lights: list of light entity ids to control (required).
- motion_sensors: list of binary_sensor ids used to detect motion.
- illumination_sensors: optional sensors used to measure ambient light (min/max thresholds).
- night_scene/on_scene/off_scene: optional scene entity ids used for night or normal activations.
- auto_turn_on / auto_turn_off: booleans to enable/disable automatic actions.
- min_illumination, max_illumination, min_elevation: numeric thresholds.

Example:
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

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
light:
  module: light
  class: LightControl
  # options:
  # auto_turn_off: True
  # auto_turn_on: True
  # fluxer_switch: <value>
  # lights: []
  # max_illumination: 150
  # min_elevation: 10
  # min_illumination: 25
  # night_scene: <value>
  # off_scene: <value>
  # on_scene: <value>
```

## Options

| key | default |
| --- | --- |
| `auto_turn_off` | `True` |
| `auto_turn_on` | `True` |
| `fluxer_switch` | `None` |
| `lights` | `[]` |
| `max_illumination` | `150` |
| `min_elevation` | `10` |
| `min_illumination` | `25` |
| `night_scene` | `None` |
| `off_scene` | `None` |
| `on_scene` | `None` |