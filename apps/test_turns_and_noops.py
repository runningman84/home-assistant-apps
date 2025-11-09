from tests.frigate.conftest import make_frigate_app


def test_count_switches_filters():
    state_map = {'switch.a': 'on', 'switch.b': 'off'}
    app, calls = make_frigate_app(args={'frigate_switches': ['switch.a', 'switch.b']}, state_map=state_map)
    app.get_state = lambda e, attribute=None: state_map.get(e)

    assert app.count_any_switches() == 2
    assert app.count_on_switches() == 1
    assert app.count_off_switches() == 1


def test_turn_on_switches_noop_when_all_on_and_records_when_needed():
    # all switches already on -> noop
    state_map = {'switch.a': 'on', 'switch.b': 'on'}
    app, calls = make_frigate_app(args={'frigate_switches': ['switch.a', 'switch.b']}, state_map=state_map)
    app.get_state = lambda e, attribute=None: state_map.get(e)

    calls.clear()
    app.turn_on_frigate_switches()
    assert calls == []

    # when not all on, should turn on and record internal change
    state_map = {'switch.a': 'off', 'switch.b': 'on'}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    calls.clear()
    app.turn_on_frigate_switches()
    assert ('on', 'switch.a') in calls
    assert any(c[0] == 'internal' for c in calls)


def test_turn_off_cameras_calls_service_and_noop_when_all_idle():
    # all cameras idle -> noop
    state_map = {'cam.a': 'idle', 'cam.b': 'idle'}
    app, calls = make_frigate_app(args={'frigate_cameras': ['cam.a', 'cam.b']}, state_map=state_map)
    app.get_state = lambda e, attribute=None: state_map.get(e)

    calls.clear()
    app.turn_off_frigate_cameras()
    assert calls == []

    # one streaming -> call camera.turn_off and record
    state_map = {'cam.a': 'streaming', 'cam.b': 'idle'}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    calls.clear()
    app.turn_off_frigate_cameras()
    assert any(c[0] == 'camera/turn_off' for c in calls)
    assert any(c[0] == 'internal' for c in calls)
