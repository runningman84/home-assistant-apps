from tests.temperature_sync.conftest import make_temp_sync_app


def test_sync_sets_outputs_for_numeric_value():
    state_map = {'sensor.temp': '21.5'}
    app, calls = make_temp_sync_app(args={'input': 'sensor.temp', 'outputs': ['number.a', 'number.b']}, state_map=state_map)
    app._input = 'sensor.temp'
    app._outputs = ['number.a', 'number.b']

    app.sync_temperature()
    assert any(call[0] == 'number/set_value' for call in calls)


def test_sync_ignores_invalid_input_and_logs_error():
    state_map = {'sensor.temp': 'not-a-number'}
    app, calls = make_temp_sync_app(args={'input': 'sensor.temp', 'outputs': ['number.a']}, state_map=state_map)
    app._input = 'sensor.temp'
    app._outputs = ['number.a']

    app.sync_temperature()
    assert any(c[0] == 'error' for c in calls)


def test_periodic_and_sensor_callbacks_invoke_sync():
    app, calls = make_temp_sync_app(args={'input': 'sensor.temp', 'outputs': []}, state_map={})
    called = []
    app.sync_temperature = lambda: called.append('sync')

    app.periodic_time_callback({})
    app.sensor_change_callback('sensor.temp', None, 'old', 'new', {})
    assert called == ['sync', 'sync']
