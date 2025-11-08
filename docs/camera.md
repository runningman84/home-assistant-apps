# CameraImageScanner

Description
-----------
CameraImageScanner triggers image_processing scans on configured processors when sensors report activity. Useful when you want to run image pipelines on demand rather than continuously.

Minimal apps.yaml snippet
-------------------------
```yaml
camera_scanner:
  module: camera
  class: CameraImageScanner
  image_processor: image_processing.my_person_detector
  sensors:
    - binary_sensor.motion_front_door
```

Notes
-----
- See `apps/camera.py` for processing cadence and tuning parameters.

Options
-------
 - `image_processor` (entity) — default: None
 - `sensors` (list) — default: []
 - `processing_max_count` / cadence parameters are defined in `apps/camera.py` source.