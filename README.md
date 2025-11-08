# home-assistant-apps

Home Assistant utility apps implemented for AppDaemon. These small apps provide common automations such as an alarm control, climate helpers, light and power automation, camera integration and more.

This repository contains the AppDaemon application code. A sample configuration showing every app and its options is available at `sample_config/apps.yaml` and a minimal example in `sample_config/scripts_minimal.yaml`.

## Quick links

- Sample config: `sample_config/apps.yaml`
- Minimal example: `sample_config/scripts_minimal.yaml`
- App source: `apps/` directory
 - Apps reference: `APPS.md`

## Requirements

- Home Assistant (any recent release)
- AppDaemon (v3/v4 depending on your setup) and its Home Assistant plugin

## Install / Usage

1. Install and configure AppDaemon in your Home Assistant environment.
2. Copy the `apps/` folder into your AppDaemon apps directory (or point AppDaemon to this repo).
3. Review `sample_config/apps.yaml` and adapt the app entries to your entities and services.
4. Restart AppDaemon to load the apps.

## Basic contract for apps

Inputs:
- App configuration entries (usually in `apps.yaml`): entity ids, timers and optional input_booleans.

Outputs:
- Calls Home Assistant services (notify, light, scene, switch, camera, etc.) and updates internal state.

Error modes:
- Apps will log errors to AppDaemon logs. Misconfigured entity ids will result in no-op or logged warnings.

## Included apps (overview)

The `apps/` folder contains the following automations (see individual source files for full option lists):

- `alarm.py` — AlarmControl: arms/disarms automatically based on device trackers and monitors sensors (doors, motion, water, fire). Supports camera snapshots and notifications.
- `climate.py` — ClimateControl: adjusts thermostats based on open windows/doors, presence and mode (vacation/guest).
- `light.py` / `light_switch.py` / `hello.py` — LightControl variants: motion-based lighting, night/evening scenes and manual switches.
- `power.py` — PowerControl: switches devices off based on motion and presence to save energy.
- `camera.py`, `frigate.py` — Camera helpers and Frigate integration helpers.
- `telegram.py` — Telegram notification helpers.
- `waste.py`, `dog.py`, `weather.py`, `temperature_sync.py`, `cleanup.py`, `awtrix.py`, `heat.py` — Misc small helpers and automations; browse the `apps/` folder for details.

## Configuration examples

See `sample_config/apps.yaml` for a full example configuration covering all available options. A minimal working configuration is available in `sample_config/scripts_minimal.yaml`.

## Contributing

Contributions welcome — please open issues or pull requests. Keep changes small and focused. If adding a new app, include a short README or docstring describing configuration keys and expected behavior.

## License

This project is provided under the terms of the repository `LICENSE` file.
