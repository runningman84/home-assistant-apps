# CameraImageScanner

CameraImageScanner app: trigger and manage image processing scans for configured cameras.

Main features:
- Trigger image_processing scans when configured sensors (e.g., motion) change.
- Manage scan scheduling, throttling and automatic stop when inactivity is detected.

Key configuration keys:
- image_processor: entity_id of an image_processing configuration to call via service.
- sensors: list of binary_sensor ids that should trigger scans.

Example:
```yaml
camera_scanner:
    module: camera
    class: CameraImageScanner
    image_processor: image_processing.my_person_detector
    sensors:
        - binary_sensor.motion_front_door
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
camera:
  module: camera
  class: CameraImageScanner
  # options:
  # image_processor: <value>
  # sensors: []
```

## Options

| key | default |
| --- | --- |
| `image_processor` | `None` |
| `sensors` | `[]` |