# TemperatureSync

TemperatureSync app: synchronize a source temperature sensor to multiple target entities.

Main features:
- Mirror a numeric temperature sensor to one or more `number` entities or setpoint controls.
- Validate numeric input and ignore invalid sensor states.

Key configuration keys:
- input: entity id of the source temperature sensor (required).
- outputs: list of target entity ids to set (e.g., number.setpoint_*).

Example:
```yaml
temperature_sync:
    module: temperature_sync
    class: TemperatureSync
    input: sensor.temperature_outside
    outputs:
        - number.setpoint_living
        - number.setpoint_bedroom
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
temperature_sync:
  module: temperature_sync
  class: TemperatureSync
  # options:
  # input: <value>
  # outputs: []
```

## Options

| key | default |
| --- | --- |
| `input` | `None` |
| `outputs` | `[]` |