# LightSwitch

LightSwitch app: translate remote button events into light control actions.

Main features:
- Listen to remote button events and translate clicks/holds into brightness, color or group toggles.
- Provide mappings for left/right groups and default lights.

Key configuration keys:
- remotes: list of remote entity ids emitting events (required).
- lights, lights_left, lights_right: lists of lights to operate for different button mappings.

Example:
```yaml
light_switch:
    module: light_switch
    class: LightSwitch
    remotes:
        - remote.left
    lights:
        - light.living
    lights_left:
        - light.left_corner
    lights_right:
        - light.right_corner
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
light_switch:
  module: light_switch
  class: LightSwitch
  # options:
  # lights: []
  # lights_left: []
  # lights_right: []
  # remotes: []
```

## Options

| key | default |
| --- | --- |
| `lights` | `[]` |
| `lights_left` | `[]` |
| `lights_right` | `[]` |
| `remotes` | `[]` |