# Cleanup

Cleanup app: performs file or resource cleanup based on configured sensors and thresholds.

Main features:
- Trigger cleanup service calls when a monitored sensor exceeds configured thresholds (file count, bytes).
- Minimal configuration, intended to call an existing cleanup script or service.

Key configuration keys:
- service: service to call to perform cleanup (e.g., script.cleanup_files).
- sensor: sensor entity that reports 'number_of_files' and 'bytes' as attributes.

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
cleanup:
  module: cleanup
  class: Cleanup
  # options:
  # limit_number_bytes: 10000000
  # limit_number_of_files: 100
  # sensor: <value>
  # service: <value>
```

## Options

| key | default |
| --- | --- |
| `limit_number_bytes` | `10000000` |
| `limit_number_of_files` | `100` |
| `sensor` | `None` |
| `service` | `None` |