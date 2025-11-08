# TelegramBotEventListener

Event listener for Telegram bot events.

## Minimal apps.yaml snippet

```yaml
telegram:
  module: telegram
  class: TelegramBotEventListener
  # options:
  # alarm_control_panel: alarm_control_panel.ha_alarm
  # alarm_pin: <value>
  # guest_control: <value>
  # user_ids: []
```

## Options

| key | default |
| --- | --- |
| `alarm_control_panel` | `alarm_control_panel.ha_alarm` |
| `alarm_pin` | `None` |
| `guest_control` | `None` |
| `user_ids` | `[]` |