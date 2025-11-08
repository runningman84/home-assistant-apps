# TelegramBotEventListener

Description
-----------
TelegramBotEventListener listens for Telegram commands and callbacks and can be used to control the alarm, request snapshots or receive notifications.

Minimal apps.yaml snippet
-------------------------
```yaml
telegram_bot:
  module: telegram
  class: TelegramBotEventListener
  user_ids:
    - 123456789
  alarm_control_panel: alarm_control_panel.ha_alarm
```

Notes
-----
- See `apps/telegram.py` for the list of available commands, callbacks and callback payload structure.

Options
-------
 - `alarm_control_panel` (entity) — default: `alarm_control_panel.ha_alarm`
 - `guest_control` (entity) — default: None
 - `alarm_pin` (str) — default: None
 - `user_ids` (list) — default: []