# TemperatureSync

Description
-----------
Copies a single input temperature sensor to one or more numeric outputs. Useful to sync setpoints or sensor values across entities.

Minimal apps.yaml snippet
-------------------------
```yaml
temperature_sync:
  module: temperature_sync
  class: TemperatureSync
  input: sensor.temperature_outside
  outputs:
    - number.setpoint_living
    - number.setpoint_bedroom
```

Options
-------
- `input` (entity) — required
- `outputs` (list) — default: []

Notes
-----
The app listens to the input sensor and periodically syncs values to configured outputs.