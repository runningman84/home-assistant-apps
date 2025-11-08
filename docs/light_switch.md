# LightSwitch

Description
-----------
LightSwitch maps physical remote events to light actions (brightness up/down, toggle, color temp). Useful for integrating button remotes.

Minimal apps.yaml snippet
-------------------------
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

Options
-------
- `remotes` (list) — default: []
- `lights`, `lights_left`, `lights_right` (lists) — defaults: []

Notes
-----
Events are expected to supply an `event_type` attribute used for mapping actions.