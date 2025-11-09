from datetime import datetime, timezone, timedelta

from apps.base import BaseApp


def make_base_app():
    """Factory used by tests to create a minimal BaseApp instance.

    Returns an object created with object.__new__(BaseApp) with required
    test attributes and stubbed hass methods attached.
    """
    app = object.__new__(BaseApp)

    # minimal attributes that BaseApp methods expect
    app.args = {}
    app._awtrix_prefixes = ["awtrix_prefix"]
    app._tts_devices = ["media.player.tts1"]
    app._alexa_media_devices = ["alexa.living_room"]
    app._alexa_monkeys = ["monkey1"]
    app._telegram_user_ids = ["12345"]
    app._notify_targets = ["phone_1"]
    app._alarm_control_panel = "alarm_control_panel.home"
    app._night_start = "23:00:00"
    app._night_end = "07:00:00"
    app._night_start_workday = "22:00:00"
    app._night_end_workday = "06:00:00"
    app._workday_sensor = None
    app._workday_tomorrow_sensor = None
    app._holiday_sensor = None
    app._language = "english"
    app._translation = {"english": {"hello": "Hello"}}
    app._opening_sensors = ["binary_sensor.door1", "binary_sensor.door2"]
    app._motion_sensors = ["binary_sensor.motion1"]
    app._media_players = ["media_player.tts1", "media_player.other"]
    app._vacuum_cleaners = ["vacuum.cleaner1"]
    app._lights = ["light.l1"]
    app._awake_sensors = ["sensor.awake1"]
    app._device_trackers = ["device_tracker.phone1"]
    app._opening_timeout = 30
    app._motion_timeout = 300
    app._tracker_timeout = 60
    app._vacation_timeout = 60
    app._awake_timeout = 60
    app._internal_change_timeout = 10
    app._external_change_timeout = 7200
    app._internal_change_timestamp = None
    app._external_change_timestamp = None
    app._internal_change_count = 0
    app._external_change_count = 0
    app._silent_control = None

    # stubs for hass.Hass methods used by BaseApp
    called = {"services": []}

    def call_service(service, **kwargs):
        called["services"].append((service, kwargs))

    def get_state(entity, attribute=None):
        # provide a few canned states
        if entity == "alarm_control_panel.home":
            return "disarmed"
        if entity in ("binary_sensor.door1", "binary_sensor.door2"):
            return "off"
        if entity == "binary_sensor.motion1":
            return "off"
        if entity == "media_player.tts1":
            return "playing" if attribute == "state" else None
        if entity == "vacuum.cleaner1":
            return "docked"
        if entity == "sun.sun":
            return 10
        if attribute == "last_updated":
            # Return a recent ISO timestamp
            return (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        return None

    def now_is_between(start, end):
        return True

    def get_seconds_since_update(entity):
        return 5

    app.call_service = call_service
    app.get_state = get_state
    app.now_is_between = now_is_between
    app.get_seconds_since_update = get_seconds_since_update
    app._called = called

    return app
