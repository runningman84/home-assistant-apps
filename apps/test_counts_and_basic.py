from tests.power.conftest import make_power_app


def test_count_switches_and_basic_turns():
    app, calls = make_power_app(args={'power_controls': ['switch.a', 'switch.b']}, state_map={'switch.a': 'on', 'switch.b': 'off'})
    app._power_controls = ['switch.a', 'switch.b']
    app.get_state = lambda e, attribute=None: 'on' if e == 'switch.a' else 'off'
    assert app.count_switches() == 2
    assert app.count_switches('on') == 1

    calls.clear()
    app.turn_on_power()
    assert any(c[0] == 'on' for c in calls)

    calls.clear()
    app.turn_off_power()
    assert any(c[0] == 'off' for c in calls)


def test_periodic_and_sensor_callbacks_trigger_update():
    app, calls = make_power_app()
    called = []
    app.update_power = lambda: called.append('u')
    app.periodic_time_callback({})
    app.sensor_change_callback('sensor.x', None, 'old', 'new', {})
    assert called == ['u', 'u']
