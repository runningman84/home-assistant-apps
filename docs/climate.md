# ClimateControl

ClimateControl app: manage HVAC devices and temperature modes based on presence, schedules and sensors.

Main features:
- Maintain different target temperatures for home, away, night, motion and vacation modes.
- Integrate external/outside temperature sensors to adjust behavior and enable summer mode.
- Respect opening sensors (windows/doors) and air-quality sensors (AQI, CO₂, VOC) to inhibit heating/cooling.
- React to motion, guest or vacation controls and to manual adjustments from GUI controls.
- Support per-mode control entities to change target temperatures via UI.

Key configuration keys (extracted from implementation):
- climate_controls: list of climate entity ids to manage (required).
- external_temperature_sensor / outside_temperature_sensor: optional sensor ids used for logic.
- home_temperature, night_temperature, away_temperature, vacation_temperature, motion_temperature: numeric targets.
- *_temperature_control: optional entity ids (number/select) used to change the respective temperature via UI.
- aqi_sensor, voc_sensor, co2_sensor: optional air-quality sensors and thresholds (aqi_threshold, voc_threshold, co2_threshold).
- summer_temperature_threshold, summer_temperature: thresholds and target for summer behavior.
- night_start, night_end, night_start_workday, night_end_workday: configurable night windows (in BaseApp defaults).

Example:
```yaml
climate_control:
    module: climate
    class: ClimateControl
    climate_controls:
        - climate.living_room
    opening_sensors:
        - binary_sensor.window_living
    home_temperature: 21
    away_temperature: 17
    vacation_temperature: 15
```

See module docstring and inline examples for usage.

## Minimal apps.yaml snippet

```yaml
climate:
  module: climate
  class: ClimateControl
  # options:
  # aqi_sensor: <value>
  # aqi_threshold: 50
  # away_hvac_mode: heat
  # away_temperature: 18
  # away_temperature_control: <value>
  # climate_controls: []
  # co2_sensor: <value>
  # co2_threshold: 800
  # external_temperature_sensor: <value>
  # fan_overheat_temperature: 22
  # home_hvac_mode: heat
  # home_temperature: 20
  # home_temperature_control: <value>
  # humidity_sensor: <value>
  # max_overheat_allowance: 0.5
  # min_temperature: 7
  # motion_duration: 300
  # motion_hvac_mode: heat
  # motion_temperature: 21
  # motion_temperature_control: <value>
  # night_hvac_mode: heat
  # night_temperature: 18
  # night_temperature_control: <value>
  # offset_temperature: 0
  # open_hvac_mode: off
  # open_temperature: 16
  # open_temperature_control: <value>
  # outside_temperature_sensor: <value>
  # summer_hvac_mode: off
  # summer_temperature: 7
  # summer_temperature_control: <value>
  # summer_temperature_threshold: 15
  # summer_temperature_threshold_tomorrow: <complex>
  # vacation_hvac_mode: heat
  # vacation_temperature: 16
  # vacation_temperature_control: <value>
  # voc_sensor: <value>
  # voc_threshold: 220
```

## Options

| key | default |
| --- | --- |
| `aqi_sensor` | `None` |
| `aqi_threshold` | `50` |
| `away_hvac_mode` | `heat` |
| `away_temperature` | `18` |
| `away_temperature_control` | `None` |
| `climate_controls` | `[]` |
| `co2_sensor` | `None` |
| `co2_threshold` | `800` |
| `external_temperature_sensor` | `None` |
| `fan_overheat_temperature` | `22` |
| `home_hvac_mode` | `heat` |
| `home_temperature` | `20` |
| `home_temperature_control` | `None` |
| `humidity_sensor` | `None` |
| `max_overheat_allowance` | `0.5` |
| `min_temperature` | `7` |
| `motion_duration` | `300` |
| `motion_hvac_mode` | `heat` |
| `motion_temperature` | `21` |
| `motion_temperature_control` | `None` |
| `night_hvac_mode` | `heat` |
| `night_temperature` | `18` |
| `night_temperature_control` | `None` |
| `offset_temperature` | `0` |
| `open_hvac_mode` | `off` |
| `open_temperature` | `16` |
| `open_temperature_control` | `None` |
| `outside_temperature_sensor` | `None` |
| `summer_hvac_mode` | `off` |
| `summer_temperature` | `7` |
| `summer_temperature_control` | `None` |
| `summer_temperature_threshold` | `15` |
| `summer_temperature_threshold_tomorrow` | `<complex>` |
| `vacation_hvac_mode` | `heat` |
| `vacation_temperature` | `16` |
| `vacation_temperature_control` | `None` |
| `voc_sensor` | `None` |
| `voc_threshold` | `220` |