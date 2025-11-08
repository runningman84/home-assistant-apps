# Cleanup

Description
-----------
Triggers a cleanup service when a sensor reports too many files or total bytes above configured limits. Useful for camera/image storage pruning.

Minimal apps.yaml snippet
-------------------------
```yaml
cleanup:
  module: cleanup
  class: Cleanup
  sensor: sensor.camera_storage
  limit_number_of_files: 200
  limit_number_bytes: 50000000
  service: script.cleanup_camera
```

Options
-------
- `limit_number_of_files` (int) — default: 100
- `limit_number_bytes` (int) — default: 10000000
- `service` (str) — cleanup service to call, default: None
- `sensor` (entity) — entity to monitor, default: None