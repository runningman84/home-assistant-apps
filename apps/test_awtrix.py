from tests.awtrix.conftest import make_awtrix_app


def test_send_mqtt_and_turn_on_off_sleep():
    prefixes = ['awtrix/dev1', 'awtrix/dev2']
    app, calls = make_awtrix_app(args={'awtrix_prefixes': prefixes})
    app.__awtrix_prefixes = prefixes

    calls.clear()
    app.send_mqtt('power', {'power': True})
    assert any(c[0] == 'mqtt/publish' for c in calls)

    calls.clear()
    app.turn_on()
    assert any(c[0] == 'mqtt/publish' for c in calls)

    calls.clear()
    app.turn_off()
    assert any(c[0] == 'mqtt/publish' for c in calls)

    calls.clear()
    app.sleep(30)
    assert any(c[0] == 'mqtt/publish' for c in calls)


def test_setup_branches_sleep_and_turn_on():
    app, calls = make_awtrix_app()
    # simulate motion present
    app.count_on_motion_sensors = lambda: 1
    app.get_last_motion = lambda: 0.0
    # ensure prefixes exist so send_mqtt will call the mqtt service
    # note: class uses double-underscore attribute so it is name-mangled
    setattr(app, '_AwtrixControl__awtrix_prefixes', ['awtrix/test'])
    app.setup()
    assert any(c[0] == 'mqtt/publish' for c in calls)

def test_setup_sleep_on_night_and_no_motion():
    app, calls = make_awtrix_app()
    # ensure name-mangled prefixes exist so send_mqtt calls mqtt/publish
    setattr(app, '_AwtrixControl__awtrix_prefixes', ['awtrix/test'])

    # night window branch -> should call sleep (mqtt publish)
    app.is_time_in_night_window = lambda: True
    app.get_seconds_until_night_end = lambda: 123
    calls.clear()
    app.setup()
    assert any(c[0] == 'mqtt/publish' for c in calls)

    # no motion and not night -> sleep 60 seconds branch
    app.is_time_in_night_window = lambda: False
    app.count_on_motion_sensors = lambda: 0
    calls.clear()
    app.setup()
    assert any(c[0] == 'mqtt/publish' for c in calls)


def test_periodic_and_sensor_callbacks_invoke_setup():
    app, calls = make_awtrix_app()

    invoked = []
    app.setup = lambda: invoked.append('setup')

    # periodic callback should call setup
    app.periodic_time_callback({})
    # sensor callback should call setup
    app.sensor_change_callback('sensor.x', 'state', 'off', 'on', {})

    assert invoked == ['setup', 'setup']

