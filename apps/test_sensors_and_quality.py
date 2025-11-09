

def make_climate_app_fixture(args=None, state_map=None):
    from apps.climate import ClimateControl
    app = object.__new__(ClimateControl)
    app.args = args or {}
    # simple state mapping helper
    state_map = state_map or {}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    # defaults for ClimateControl.initialize expectations (minimal)
    app._opening_sensors = []
    app._motion_sensors = []
    app._device_trackers = []
    app._vacation_control = None
    app._guest_control = None
    # ensure device trackers and guest control defaults exist for get_current_status
    if not hasattr(app, '_guest_control'):
        app._guest_control = None
    if not hasattr(app, '_device_trackers'):
        app._device_trackers = []
    app._night_start = "23:15:00"
    app._night_end = "08:30:00"
    app._night_start_workday = "22:15:00"
    app._night_end_workday = "06:30:00"
    app._external_temperature_sensor = None
    app._outside_temperature_sensor = None
    app._max_overheat_allowance = 0.5
    app._fan_overheat_temperature = 22.0
    app._summer_temperature_threshold = 15.0
    app._summer_temperature_threshold_tomorrow = 18.0
    app._min_temperature = 7.0
    app._aqi_sensor = app.args.get('aqi_sensor', None)
    app._aqi_threshold = int(app.args.get('aqi_threshold', 50))
    app._voc_sensor = app.args.get('voc_sensor', None)
    app._voc_threshold = int(app.args.get('voc_threshold', 220))
    app._co2_sensor = app.args.get('co2_sensor', None)
    app._co2_threshold = int(app.args.get('co2_threshold', 800))
    app._humidity_sensor = None
    app._offset_temperature = 0
    app._motion_temperature = 21
    app._motion_temperature_control = None
    app._motion_hvac_mode = 'heat'
    app._motion_duration = 300
    app._home_temperature = 20
    app._home_temperature_control = None
    app._home_hvac_mode = 'heat'
    app._night_temperature = 18
    app._night_temperature_control = None
    app._night_hvac_mode = 'heat'
    app._away_temperature = 18
    app._away_temperature_control = None
    app._away_hvac_mode = 'heat'
    app._vacation_temperature = 16
    app._vacation_hvac_mode = 'heat'
    app._vacation_temperature_control = None
    app._open_temperature = 16
    app._open_hvac_mode = 'off'
    app._open_temperature_control = None
    app._summer_temperature = 7
    app._summer_hvac_mode = 'off'
    app._summer_temperature_control = None
    app._holiday_sensor = None
    app._workday_sensor = None
    app._outside_temperature_sensor = None
    app._workday_tomorrow_sensor = None
    app._summer_temperature_threshold_tomorrow = app._summer_temperature_threshold + 3
    app._night_start_workday = "22:15:00"
    app._night_end_workday = "06:30:00"
    app._aqi_sensor = app.args.get('aqi_sensor', None)
    app._voc_sensor = app.args.get('voc_sensor', None)
    app._co2_sensor = app.args.get('co2_sensor', None)
    return app


def test_aqi_voc_co2_measurements_and_thresholds():
    app = make_climate_app_fixture(
        args={
            'aqi_sensor': 'sensor.aqi',
            'voc_sensor': 'sensor.voc',
            'co2_sensor': 'sensor.co2',
            'aqi_threshold': 50,
            'voc_threshold': 200,
            'co2_threshold': 800,
        },
        state_map={
            'sensor.aqi': '10',
            'sensor.voc': '100',
            'sensor.co2': '700'
        }
    )

    assert app.get_aqi_measurement() == 10
    assert app.get_voc_measurement() == 100
    assert app.get_co2_measurement() == 700
    assert app.is_aqi_okay() is True
    assert app.is_voc_okay() is True
    assert app.is_co2_okay() is True

    # exceed thresholds
    app.get_state = lambda e, attribute=None: '1000' if e == 'sensor.co2' else '9999'
    assert app.get_co2_measurement() == 1000
    assert app.is_co2_okay() is False


def test_external_and_outside_temperatures():
    app = make_climate_app_fixture(
        args={'outside_temperature_sensor': 'sensor.out'},
        state_map={'sensor.out': '12', 'weather.forecast_home': 15}
    )

    assert app.get_external_temperature() is None  # no _external set
    assert app.get_outside_temperature() == 15.0

    # when both sensor and forecast present, take max
    app._outside_temperature_sensor = 'sensor.out'
    app.get_state = lambda e, attribute=None: '18' if e == 'sensor.out' else 15
    assert app.get_outside_temperature() == 18.0
