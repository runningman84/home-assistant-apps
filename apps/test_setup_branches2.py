from tests.frigate.conftest import make_frigate_app


def test_setup_turns_on_on_opening():
    app, calls = make_frigate_app()
    app.is_internal_change_allowed = lambda: True
    app._auto_turn_on_opening = True
    app._frigate_cameras = ['c1']
    app._frigate_switches = ['s1']
    # count_opening_sensors('on') > 0 and count_opening_sensors() > 0
    app.count_opening_sensors = lambda state=None: 1 if state == 'on' else 1
    app.turn_on_frigate = lambda: calls.append(('turn_on', 'opening'))

    app.setup()
    assert ('turn_on', 'opening') in calls


def test_setup_turns_on_on_alarm_any_flag():
    app, calls = make_frigate_app()
    app.is_internal_change_allowed = lambda: True
    app._auto_turn_on_alarm = True
    app._frigate_cameras = ['c1']
    app._frigate_switches = ['s1']
    # any of the alarm predicates should trigger
    app.is_alarm_triggered = lambda: False
    app.is_alarm_arming = lambda: False
    app.is_alarm_pending = lambda: True
    app.is_alarm_armed = lambda: False
    app.turn_on_frigate = lambda: calls.append(('turn_on', 'alarm'))

    app.setup()
    assert ('turn_on', 'alarm') in calls


def test_setup_turns_off_on_no_openings_and_on_alarm_disarmed():
    app, calls = make_frigate_app()
    app.is_internal_change_allowed = lambda: True
    app._auto_turn_off_opening = True
    app._auto_turn_off_alarm = True
    app._frigate_cameras = ['c1']
    app._frigate_switches = ['s1']

    # no openings -> off
    app.count_opening_sensors = lambda state=None: (2 if state is None else 2 if state == 'off' else 0)
    app.turn_off_frigate = lambda: calls.append(('turn_off', 'opening'))
    app.setup()
    assert ('turn_off', 'opening') in calls

    # alarm disarmed should also turn off
    calls.clear()
    app.is_alarm_disarmed = lambda: True
    app.count_opening_sensors = lambda state=None: 0
    app.turn_off_frigate = lambda: calls.append(('turn_off', 'alarm_dis'))
    app.setup()
    assert ('turn_off', 'alarm_dis') in calls


def test_turn_on_cameras_and_turn_off_switches_behavior():
    state_map = {'cam.a': 'idle', 'cam.b': 'idle', 's1': 'on', 's2': 'off'}
    app, calls = make_frigate_app(args={'frigate_cameras': ['cam.a', 'cam.b'], 'frigate_switches': ['s1', 's2']}, state_map=state_map)
    app.get_state = lambda e, attribute=None: state_map.get(e)

    calls.clear()
    app.turn_on_frigate_cameras()
    assert any(c[0] == 'camera/turn_on' for c in calls)
    assert any(c[0] == 'internal' for c in calls)

    calls.clear()
    app.turn_off_frigate_switches()
    assert ('off', 's1') in calls or ('off', 's2') in calls
