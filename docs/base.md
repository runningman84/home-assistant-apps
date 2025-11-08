# BaseApp

Description
-----------
`BaseApp` provides common utilities used by most apps: sensor lists, time/window helpers, notification helpers, internal/external change recording, and shared timeouts.

Options (common for many apps)
-----------------------------
- `opening_sensors` (list) — default: []
- `motion_sensors` (list) — default: []
- `illumination_sensors` (list) — default: []
- `awake_sensors` (list) — default: []
- `device_trackers` (list) — default: []
- `media_players` (list) — default: []
- `vacation_control` (entity) — default: None
- `guest_control` (entity) — default: None
- `alarm_control_panel` (entity) — default: None
- `opening_timeout` (seconds) — default: 30
- `motion_timeout` (seconds) — default: 300
- `tracker_timeout` (seconds) — default: 60
- `vacation_timeout` (seconds) — default: 60
- `awake_timeout` (seconds) — default: 900
- `notify_service` (service) — default: None
- `telegram_user_ids` (list) — default: []
- `awtrix_prefixes` (list) — default: []
- `language` (str) — default: "english"
- `night_start`, `night_end` (time) — defaults: "23:15:00" / "06:30:00"
- `external_change_timeout`, `internal_change_timeout` (seconds) — defaults: 7200, 10

Notes
-----
This file isn't intended to be added directly to `apps.yaml` — it's the shared base class. Many apps accept the options listed above; check each app's doc for specifics.