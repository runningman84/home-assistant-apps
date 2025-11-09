from tests.frigate.conftest import make_frigate_app


def test_setup_turns_off_on_no_motion():
    app, calls = make_frigate_app()
    app.is_internal_change_allowed = lambda: True
    app._auto_turn_off_motion = True
    app._frigate_cameras = ['c1']
    app._frigate_switches = ['s1']
    app.count_motion_sensors = lambda state=None: 0 if state == 'on' else 2
    app.count_motion_sensors = lambda state=None: 2 if state is None else 0 if state == 'on' else 2
    # ensure count_motion_sensors('off') == count_motion_sensors() and > 0
    app.count_motion_sensors = lambda state=None: 2 if state is None else (0 if state == 'on' else 2)
    app.turn_off_frigate = lambda: calls.append(('turn_off', 'frigate'))

    app.setup()
    assert ('turn_off', 'frigate') in calls


def test_periodic_and_sensor_call_setup():
    app, calls = make_frigate_app()
    called = []
    app.setup = lambda: called.append('s')
    app.periodic_time_callback({})
    app.sensor_change_callback('ent', None, 'old', 'new', {})
    assert called == ['s', 's']
