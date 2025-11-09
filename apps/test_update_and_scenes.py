from tests.light.conftest import make_light_app


def test_update_turns_off_when_nobody_home_or_vacation():
    app, calls = make_light_app(args={'lights': ['light.l1']})
    # nobody home
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: True
    app._lights = ['light.l1']
    calls.clear()
    app.update_lights()
    assert any(c[0] == 'off' for c in calls)

    # vacation mode
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: True
    calls.clear()
    app.update_lights()
    assert any(c[0] == 'off' for c in calls)


def test_turn_on_uses_scene_or_lights_and_respects_auto_flag():
    app, calls = make_light_app(args={'lights': ['light.l1'], 'on_scene': 'scene.on'})
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_on_motion_sensors = lambda: 1
    app.count_motion_sensors = lambda: 1
    # below illumination triggers
    app._illumination_sensors = ['sensor.l1']
    app.get_state = lambda e, attribute=None: '0'
    calls.clear()
    app._on_scene = 'scene.on'
    app.turn_on_lights()
    assert any(c[0] == 'on' and c[1] == 'scene.on' for c in calls)

    # if auto turn on disabled nothing happens
    calls.clear()
    app._on_scene = None
    app._auto_turn_on = False
    app.turn_on_lights()
    assert not any(c[0] == 'on' for c in calls)


def test_count_lights_and_callbacks_and_initialize():
    # initialize with listeners should not raise
    from apps.light import LightControl
    app = object.__new__(LightControl)
    app.args = {'lights': ['light.l1'], 'motion_sensors': ['binary_sensor.m']}
    app.listen_state = lambda *a, **k: None
    app.run_every = lambda *a, **k: None
    app.log = lambda *a, **k: None
    app.get_state = lambda e, attribute=None: 'on' if e == 'light.l1' else None
    app.initialize()

    # test count_lights
    app2, calls = make_light_app(args={'lights': ['light.l1', 'light.l2']}, state_map={'light.l1': 'on', 'light.l2': 'off'})
    app2._lights = ['light.l1', 'light.l2']
    app2.get_state = lambda e, attribute=None: 'on' if e == 'light.l1' else 'off'
    assert app2.count_lights() == 2
    assert app2.count_lights('on') == 1


def test_update_turns_off_on_motion_timeout():
    app, calls = make_light_app(args={'lights': ['light.l1']})
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.is_alarm_armed_away = lambda: False
    app.is_alarm_armed_vacation = lambda: False
    app.is_alarm_triggered = lambda: False
    app.is_alarm_pending = lambda: False
    # simulate no motion on sensors but some motion recorded recently
    app.count_on_motion_sensors = lambda: 0
    app.count_motion_sensors = lambda: 1
    app.get_last_motion = lambda: 123.45
    app.turn_off_lights = lambda: calls.append(('off', 'all'))
    calls.clear()
    app.update_lights()
    assert ('off', 'all') in calls


def test_update_noop_on_alarm_triggered_or_pending():
    app, calls = make_light_app(args={'lights': ['light.l1']})
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_on_motion_sensors = lambda: 1
    app.count_motion_sensors = lambda: 1
    app.is_alarm_triggered = lambda: True
    app.is_alarm_pending = lambda: False
    calls.clear()
    app.update_lights()
    # should not call turn_on/turn_off
    assert calls == []


def test_turn_on_night_scene_and_turn_off_lights_loop():
    app, calls = make_light_app(args={'lights': ['light.l1', 'light.l2']})
    app._night_scene = 'scene.night'
    app.is_time_in_night_window = lambda: True
    def count_lights(state=None):
        return 2 if state is None else 0
    app.count_lights = count_lights
    calls.clear()
    app.turn_on_lights()
    assert any(c[0] == 'on' and c[1] == 'scene.night' for c in calls)

    # test turn_off_lights loops lights when off_scene is None
    calls.clear()
    app._off_scene = None
    app._lights = ['light.l1', 'light.l2']
    app.is_auto_turn_off_disabled = lambda: False
    app.turn_off_lights()
    assert any(c[0] == 'off' and c[1] == 'light.l1' for c in calls)


