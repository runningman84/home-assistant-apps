from apps.light import LightControl


def test_initialize_registers_many_listeners():
    app = object.__new__(LightControl)
    app.args = {
        'lights': ['light.a'],
        'motion_sensors': ['binary_sensor.m1'],
        'illumination_sensors': ['sensor.i1'],
        'media_players': ['media.player1'],
        'device_trackers': ['device_tracker.t1'],
        'vacation_control': 'input_boolean.vac',
        'fluxer_switch': 'switch.flux',
        'on_scene': 'scene.on',
        'off_scene': 'scene.off',
        'night_scene': 'scene.night',
        'alarm_control_panel': 'alarm.panel'
    }

    listened = []
    app.listen_state = lambda *a, **k: listened.append((a, k))
    app.run_every = lambda *a, **k: None
    app.log = lambda *a, **k: None
    app.get_state = lambda e, attribute=None: None

    # Should not raise and should register many listeners
    app.initialize()
    assert len(listened) >= 5


def test_turn_on_turns_each_light_when_no_scene():
    app, calls = __import__('tests.light.conftest', fromlist=['make_light_app']).make_light_app()
    # configure app for per-light activation
    app._lights = ['light.a', 'light.b']
    app._on_scene = None
    app.is_time_in_night_window = lambda: False
    # count_lights indicates some are off
    app.count_lights = lambda state=None: 2 if state is None else 0
    calls.clear()
    app.turn_on_lights()
    assert any(c[0] == 'on' and c[1] == 'light.a' for c in calls)
    assert any(c[0] == 'on' and c[1] == 'light.b' for c in calls)


def test_auto_flag_accessors():
    app, _ = __import__('tests.light.conftest', fromlist=['make_light_app']).make_light_app()
    app._auto_turn_on = True
    app._auto_turn_off = False
    assert app.is_auto_turn_on_enabled() is True
    assert app.is_auto_turn_off_enabled() is False
    assert app.is_auto_turn_on_disabled() is False
    assert app.is_auto_turn_off_disabled() is True
