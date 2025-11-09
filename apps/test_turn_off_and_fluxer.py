from tests.light.conftest import make_light_app


def test_turn_off_uses_off_scene_or_lights_and_respects_auto_flag():
    app, calls = make_light_app(args={'lights': ['light.l1'], 'off_scene': 'scene.off'})
    app._lights = ['light.l1']
    app.is_auto_turn_off_disabled = lambda: False
    # simulate some lights on
    app.count_lights = lambda state=None: 0 if state == 'off' else 1
    calls.clear()
    app.turn_off_lights()
    assert any(c[0] == 'on' and c[1] == 'scene.off' for c in calls)

    # if auto turn off disabled nothing happens
    calls.clear()
    app.is_auto_turn_off_disabled = lambda: True
    app.turn_off_lights()
    assert not any(c[0] == 'off' for c in calls)


def test_flux_change_callback_turns_fluxer_on_off():
    app, calls = make_light_app(args={'fluxer_switch': 'switch.flux'})
    app._fluxer_switch = 'switch.flux'
    app.get_state = lambda e, attribute=None: 'on' if e == 'switch.flux' else None
    calls.clear()
    # simulate alarm pending -> should turn off fluxer
    app.flux_change_callback('alarm', None, 'disarmed', 'pending', {})
    assert any(c[0] == 'off' and c[1] == 'switch.flux' for c in calls)

    # simulate alarm disarmed -> if fluxer off, turn on
    app.get_state = lambda e, attribute=None: 'off' if e == 'switch.flux' else None
    calls.clear()
    app.flux_change_callback('alarm', None, 'pending', 'disarmed', {})
    assert any(c[0] == 'on' and c[1] == 'switch.flux' for c in calls)


def test_periodic_and_sensor_callbacks_call_update():
    app, calls = make_light_app()
    called = []
    app.update_lights = lambda: called.append('u')
    app.periodic_time_callback({})
    app.sensor_change_callback('sensor.x', None, 'old', 'new', {})
    assert called == ['u', 'u']


def test_turn_on_when_all_already_on_and_fluxer_none():
    app, calls = make_light_app()
    # count_lights returns equal counts -> all on
    app.count_lights = lambda state=None: 1
    calls.clear()
    app.turn_on_lights()
    assert calls == []
    # flux_change no-op when None
    app._fluxer_switch = None
    # should not raise
    app.flux_change_callback('alarm', None, 'x', 'pending', {})
    assert True
