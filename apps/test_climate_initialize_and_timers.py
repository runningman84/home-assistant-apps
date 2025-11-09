

def test_initialize_registers_listeners_and_schedulers():
    # Create a raw ClimateControl instance and call initialize() with many args
    from apps.climate import ClimateControl
    app = object.__new__(ClimateControl)

    # Prepare args to exercise most branches
    app.args = {
        'climate_controls': ['climate.l1'],
        'opening_sensors': ['binary_sensor.win1'],
        'motion_sensors': ['binary_sensor.motion1'],
        'device_trackers': ['device_tracker.t1'],
        'vacation_control': 'input_boolean.vac',
        'guest_control': 'input_boolean.guest',
        'aqi_sensor': 'sensor.aqi',
        'voc_sensor': 'sensor.voc',
        'co2_sensor': 'sensor.co2',
        'external_temperature_sensor': 'sensor.ext',
        'outside_temperature_sensor': 'sensor.out',
        'home_temperature_control': 'input_number.home_temp',
        'night_temperature_control': 'input_number.night_temp',
        'motion_temperature_control': 'input_number.motion_temp'
    }

    # Capture calls to listeners and schedulers
    listened = []
    def listen_state(callback, entity, **kwargs):
        listened.append((entity, kwargs))

    run_daily_calls = []
    def run_daily(callback, runtime):
        run_daily_calls.append(runtime)

    run_every_calls = []
    def run_every(callback, when, interval):
        run_every_calls.append((when, interval))

    # simple parse_time stub
    app.parse_time = lambda s: s

    # minimal get_state that returns sensible values when initialize asks
    def get_state(entity, attribute=None):
        if entity == 'binary_sensor.zigbee2mqtt_bridge_connection_state':
            return 'on'
        if entity in ('input_number.home_temp', 'input_number.night_temp', 'input_number.motion_temp'):
            return '20'
        return None

    app.listen_state = listen_state
    app.run_daily = run_daily
    app.run_every = run_every
    app.get_state = get_state
    app.call_service = lambda *a, **k: None
    app.log = lambda *a, **k: None
    app.parse_time = lambda s: s

    # Should not raise
    app.initialize()

    # verify that listeners and schedulers were registered
    assert any('binary_sensor.win1' == e for e, _ in listened)
    assert any('device_tracker.t1' == e for e, _ in listened)
    assert len(run_daily_calls) >= 1
    assert len(run_every_calls) == 1
