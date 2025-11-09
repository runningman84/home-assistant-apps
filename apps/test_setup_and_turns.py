from tests.frigate.conftest import make_frigate_app


def test_count_helpers_and_turns():
    state_map = {
        'cam.a': 'idle',
        'cam.b': 'streaming',
        ('cam.a', None): 'idle'
    }
    app, calls = make_frigate_app(args={'frigate_switches': ['switch.a'], 'frigate_cameras': ['cam.a', 'cam.b']}, state_map=state_map)
    app.get_state = lambda e, attribute=None: state_map.get(e) if attribute is None else state_map.get((e, attribute))

    assert app.count_any_cameras() == 2
    assert app.count_streaming_cameras() == 1

    calls.clear()
    app.turn_on_frigate_switches()
    assert ('on', 'switch.a') in calls

    calls.clear()
    app.turn_off_frigate_cameras()
    assert any(c[0] == 'camera/turn_off' for c in calls)


def test_setup_turns_on_on_motion():
    app, calls = make_frigate_app()
    app.is_internal_change_allowed = lambda: True
    app._auto_turn_on_motion = True
    app._frigate_cameras = ['c1']
    app._frigate_switches = ['s1']
    app.count_motion_sensors = lambda state=None: 1 if state == 'on' else 1
    app.turn_on_frigate = lambda: calls.append(('turn_on', 'frigate'))

    app.setup()
    assert ('turn_on', 'frigate') in calls
