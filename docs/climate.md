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
- home_temperature, night_temperature, away_temperature, vacation_temperature, motion_temperature: numeric targets for heating mode.
- home_temperature_cooling, night_temperature_cooling, etc.: numeric targets for cooling mode (defaults to cooling_temperature if not set).
- cooling_temperature: default cooling target (default: 22°C, used when status-specific cooling temperature not configured).
- *_hvac_mode: HVAC mode for heating (e.g., home_hvac_mode, default: 'heat').
- *_hvac_mode_cooling: HVAC mode for cooling (e.g., home_hvac_mode_cooling, default: 'cool').
- *_temperature_control: optional entity id (number/select) to change heating temperature via UI for that status.
- *_temperature_control_cooling: optional entity id (number/select) to change cooling temperature via UI for that status.
- min_temperature_heating, max_temperature_heating: temperature bounds for heating (default: 7°C - 30°C).
- min_temperature_cooling, max_temperature_cooling: temperature bounds for cooling (default: 16°C - 30°C).
- offset_temperature_heating, offset_temperature_cooling: static temperature offsets for calibration (default: 0°C).
- enable_pid: enable PID controller for dynamic temperature adjustment (default: false).
- pid_kp, pid_ki, pid_kd: PID controller gains (defaults: 1.0, 0.1, 0.05).
- pid_output_limit: maximum PID offset in °C (default: 5.0).
- aqi_sensor, voc_sensor, co2_sensor: optional air-quality sensors and thresholds (aqi_threshold, voc_threshold, co2_threshold).
- summer_temperature_threshold: threshold for summer detection (used for cooling activation logic).
- min_outside_temperature_for_cooling: minimum outside temperature required to enable cooling (default: 22°C).
- min_inside_temperature_for_cooling: minimum inside temperature required to enable cooling (default: 21°C).
- overdrive_mode, overdrive_heating_temperature, overdrive_cooling_temperature: aggressive heating/cooling targets.
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
    # Heating temperatures for each status
    home_temperature: 21
    away_temperature: 17
    vacation_temperature: 15
    night_temperature: 18            # Optional: defaults shown in code
    motion_temperature: 21           # Optional: defaults shown in code
    # Cooling temperatures for each status (optional, falls back to cooling_temperature)
    home_temperature_cooling: 22     # Optional: cooling target for home status
    away_temperature_cooling: 24     # Optional: cooling target for away status
    night_temperature_cooling: 23    # Optional: cooling target for night status
    # Default cooling temperature (used when status-specific cooling temp not configured)
    cooling_temperature: 22          # Optional: default cooling target (default: 22°C)
    # Optional: HVAC modes for heating (default: 'heat')
    home_hvac_mode: heat
    away_hvac_mode: heat
    # Optional: HVAC modes for cooling (default: 'cool')
    home_hvac_mode_cooling: cool
    away_hvac_mode_cooling: off      # Turn off cooling when away to save energy
    # Optional: UI controls for heating temperatures
    home_temperature_control: input_number.climate_home_heating
    # Optional: UI controls for cooling temperatures
    home_temperature_control_cooling: input_number.climate_home_cooling
    min_temperature_heating: 7       # Optional: minimum for heating (default: 7°C)
    max_temperature_heating: 30      # Optional: maximum for heating (default: 30°C)
    min_temperature_cooling: 16      # Optional: minimum for cooling (default: 16°C)
    max_temperature_cooling: 30      # Optional: maximum for cooling (default: 30°C)
    offset_temperature_heating: -2   # Optional: calibration offset for heating (default: 0°C)
    offset_temperature_cooling: 0    # Optional: calibration offset for cooling (default: 0°C)
    # Optional: Enable PID controller for dynamic temperature adjustment (disabled by default)
    enable_pid: false                # Default: false - set to true to enable
    pid_kp: 1.0                      # Default: 1.0 - Proportional gain
    pid_ki: 0.1                      # Default: 0.1 - Integral gain
    pid_kd: 0.05                     # Default: 0.05 - Derivative gain
    pid_output_limit: 5.0            # Default: 5.0 - Maximum PID offset in °C
    # Optional: Enable overdrive for aggressive heating/cooling
    overdrive_mode: true
    overdrive_heating_temperature: 30  # Used when HVAC mode is 'heat'
    overdrive_cooling_temperature: 16  # Used when HVAC mode is 'cool'
    # Optional: Prevent cooling if temperatures are below thresholds
    min_outside_temperature_for_cooling: 22  # Default: 22°C
    min_inside_temperature_for_cooling: 21   # Default: 21°C
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
  # away_hvac_mode_cooling: cool
  # away_temperature: 18
  # away_temperature_control: <value>
  # away_temperature_control_cooling: <value>
  # away_temperature_cooling: <complex>
  # cleanup_air_at_night: True
  # climate_controls: []
  # co2_sensor: <value>
  # co2_threshold: 800
  # cooling_temperature: 22
  # cooling_temperature_control: <value>
  # enable_pid: False
  # external_temperature_sensor: <value>
  # fan_overheat_temperature: 22
  # home_hvac_mode: heat
  # home_hvac_mode_cooling: cool
  # home_temperature: 20
  # home_temperature_control: <value>
  # home_temperature_control_cooling: <value>
  # home_temperature_cooling: <complex>
  # humidity_sensor: <value>
  # internal_change_timeout: 60
  # max_overheat_allowance: 0.5
  # max_temperature_cooling: 30
  # max_temperature_heating: 30
  # min_inside_temperature_for_cooling: 20
  # min_outside_temperature_for_cooling: 23.0
  # min_temperature_cooling: 16
  # min_temperature_heating: 7
  # motion_duration: 300
  # motion_hvac_mode: heat
  # motion_hvac_mode_cooling: cool
  # motion_temperature: 21
  # motion_temperature_control: <value>
  # motion_temperature_control_cooling: <value>
  # motion_temperature_cooling: <complex>
  # night_hvac_mode: heat
  # night_hvac_mode_cooling: cool
  # night_temperature: 18
  # night_temperature_control: <value>
  # night_temperature_control_cooling: <value>
  # night_temperature_cooling: <complex>
  # offset_temperature_cooling: 0
  # offset_temperature_heating: 0
  # open_hvac_mode: off
  # open_hvac_mode_cooling: off
  # open_temperature: 16
  # open_temperature_control: <value>
  # open_temperature_control_cooling: <value>
  # open_temperature_cooling: <complex>
  # outside_temperature_sensor: <value>
  # overdrive_cooling_temperature: 16
  # overdrive_heating_temperature: 30
  # overdrive_mode: False
  # pid_kd: 0.05
  # pid_ki: 0.1
  # pid_kp: 1.0
  # pid_output_limit: 6.0
  # summer_temperature_threshold: 15
  # summer_temperature_threshold_tomorrow: <complex>
  # vacation_hvac_mode: heat
  # vacation_hvac_mode_cooling: off
  # vacation_temperature: 16
  # vacation_temperature_control: <value>
  # vacation_temperature_control_cooling: <value>
  # vacation_temperature_cooling: <complex>
  # voc_sensor: <value>
  # voc_threshold: 220
```

## Options

| key | default |
| --- | --- |
| `aqi_sensor` | `None` |
| `aqi_threshold` | `50` |
| `away_hvac_mode` | `heat` |
| `away_hvac_mode_cooling` | `cool` |
| `away_temperature` | `18` |
| `away_temperature_control` | `None` |
| `away_temperature_control_cooling` | `None` |
| `away_temperature_cooling` | `<complex>` |
| `cleanup_air_at_night` | `True` |
| `climate_controls` | `[]` |
| `co2_sensor` | `None` |
| `co2_threshold` | `800` |
| `cooling_temperature` | `22` |
| `cooling_temperature_control` | `None` |
| `enable_pid` | `False` |
| `external_temperature_sensor` | `None` |
| `fan_overheat_temperature` | `22` |
| `home_hvac_mode` | `heat` |
| `home_hvac_mode_cooling` | `cool` |
| `home_temperature` | `20` |
| `home_temperature_control` | `None` |
| `home_temperature_control_cooling` | `None` |
| `home_temperature_cooling` | `<complex>` |
| `humidity_sensor` | `None` |
| `internal_change_timeout` | `60` |
| `max_overheat_allowance` | `0.5` |
| `max_temperature_cooling` | `30` |
| `max_temperature_heating` | `30` |
| `min_inside_temperature_for_cooling` | `20` |
| `min_outside_temperature_for_cooling` | `23.0` |
| `min_temperature_cooling` | `16` |
| `min_temperature_heating` | `7` |
| `motion_duration` | `300` |
| `motion_hvac_mode` | `heat` |
| `motion_hvac_mode_cooling` | `cool` |
| `motion_temperature` | `21` |
| `motion_temperature_control` | `None` |
| `motion_temperature_control_cooling` | `None` |
| `motion_temperature_cooling` | `<complex>` |
| `night_hvac_mode` | `heat` |
| `night_hvac_mode_cooling` | `cool` |
| `night_temperature` | `18` |
| `night_temperature_control` | `None` |
| `night_temperature_control_cooling` | `None` |
| `night_temperature_cooling` | `<complex>` |
| `offset_temperature_cooling` | `0` |
| `offset_temperature_heating` | `0` |
| `open_hvac_mode` | `off` |
| `open_hvac_mode_cooling` | `off` |
| `open_temperature` | `16` |
| `open_temperature_control` | `None` |
| `open_temperature_control_cooling` | `None` |
| `open_temperature_cooling` | `<complex>` |
| `outside_temperature_sensor` | `None` |
| `overdrive_cooling_temperature` | `16` |
| `overdrive_heating_temperature` | `30` |
| `overdrive_mode` | `False` |
| `pid_kd` | `0.05` |
| `pid_ki` | `0.1` |
| `pid_kp` | `1.0` |
| `pid_output_limit` | `6.0` |
| `summer_temperature_threshold` | `15` |
| `summer_temperature_threshold_tomorrow` | `<complex>` |
| `vacation_hvac_mode` | `heat` |
| `vacation_hvac_mode_cooling` | `off` |
| `vacation_temperature` | `16` |
| `vacation_temperature_control` | `None` |
| `vacation_temperature_control_cooling` | `None` |
| `vacation_temperature_cooling` | `<complex>` |
| `voc_sensor` | `None` |
| `voc_threshold` | `220` |