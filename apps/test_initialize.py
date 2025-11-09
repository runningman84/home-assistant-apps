from tests.base.factories import make_base_app


class InitDummy(make_base_app().__class__):
    pass


def test_initialize_sets_many_defaults_and_logs():
    # create a new DummyBase-like object but we will use object.__new__ pattern
    app = object.__new__(InitDummy)

    # Provide many non-default args to trigger branches in initialize
    app.args = {
        "opening_sensors": ["s1"],
        "motion_sensors": ["m1"],
        "illumination_sensors": ["il1"],
        "awake_sensors": ["a1"],
        "device_trackers": ["d1"],
        "media_players": ["mp1"],
        "vacuum_cleaners": ["v1"],
        "lights": ["l1"],
        "vacation_control": "vac1",
        "guest_control": "guest1",
        "alarm_control_panel": "alarm.home",
        "opening_timeout": 5,
        "motion_timeout": 6,
        "tracker_timeout": 7,
        "vacation_timeout": 8,
        "awake_timeout": 9,
        "notify_service": "notify.x",
        "notify_title": "Title {}",
        "telegram_user_ids": ["t"],
        "notify_targets": ["nt"],
        "alexa_media_devices": ["alex"],
        "alexa_monkeys": ["mon"],
        "tts_devices": ["tts1"],
        "silent_control": "sc",
        "awtrix_prefixes": ["pref"],
        "language": "english",
        "night_start": "22:00:00",
        "night_end": "06:00:00",
        "night_start_workday": "21:00:00",
        "night_end_workday": "05:00:00",
        "workday_sensor": None,
        "workday_tomorrow_sensor": None,
        "holiday_sensor": None,
        "external_change_timeout": 3600,
        "internal_change_timeout": 5,
    }

    # stub out methods used during initialize that would otherwise call hass
    app.log = lambda *a, **k: None
    app.count_home_device_trackers = lambda: 1
    app.count_not_home_device_trackers = lambda: 0
    app.in_guest_mode = lambda: False
    app.in_vacation_mode = lambda: False

    # Now call initialize which should set numerous attributes without error
    app.initialize()

    # spot checks to ensure values were set from args
    assert app._opening_sensors == ["s1"]
    assert app._motion_sensors == ["m1"]
    assert app._opening_timeout == 5
    assert app._motion_timeout == 6
    assert app._language == "english"
    assert app._awtrix_prefixes == ["pref"]