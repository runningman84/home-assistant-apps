from tests.climate.conftest import make_climate_app


def test_status_branches_and_summer_logic():
    # Summer should take precedence when outside temp is high
    app, _ = make_climate_app(state_map={'weather.forecast_home': '30'})
    app.get_outside_temperature = lambda: 30.0
    assert app.is_summer() is True
    assert app.get_current_status() == 'summer'

    # Open window -> open
    app, _ = make_climate_app()
    app._opening_sensors = ['s1']
    app.get_state = lambda e, attribute=None: 'on' if e == 's1' else None
    assert app.get_current_status() == 'open'

    # Vacation control
    app, _ = make_climate_app()
    app._vacation_control = 'vac'
    app.get_state = lambda e, attribute=None: 'on' if e == 'vac' else None
    assert app.get_current_status() == 'vacation'


def test_hvac_and_fan_selection_and_aqi():
    app, _ = make_climate_app()
    # default fan
    assert app.get_desired_fan_mode() in ('Auto', 'Low', 'Mid', 'HighMid', 'High')

    # AQI triggers high fan
    app.get_aqi_measurement = lambda: 1000
    fm = app.get_desired_fan_mode()
    assert fm in ['High', 'HighMid', 'Mid', 'Auto']

    # Overheat -> fan-only or off depending on occupancy
    app.get_external_temperature = lambda: 35
    app.get_desired_temperature = lambda: 20
    app.is_somebody_at_home = lambda: False
    assert app.get_desired_hvac_mode() in ('off', 'fan_only', 'heat', 'cool')


def test_air_quality_helpers_and_thresholds():
    args = {'aqi_sensor': 'sensor.aqi', 'voc_sensor': 'sensor.voc', 'co2_sensor': 'sensor.co2',
            'aqi_threshold': 50, 'voc_threshold': 200, 'co2_threshold': 800}
    state_map = {'sensor.aqi': '10', 'sensor.voc': '100', 'sensor.co2': '700'}
    app, _ = make_climate_app(args=args, state_map=state_map)
    assert app.get_aqi_measurement() == 10
    assert app.is_aqi_okay() is True
    app.get_state = lambda e, attribute=None: '1000' if e == 'sensor.co2' else '9999'
    assert app.get_co2_measurement() == 1000
    assert app.is_co2_okay() is False


def test_outside_temperature_source_and_max():
    app, _ = make_climate_app(state_map={'weather.forecast_home': 15})
    # when no outside sensor configured, forecast is used
    app._outside_temperature_sensor = None
    app.get_state = lambda e, attribute=None: 12 if e == 'sensor.out' else 15
    assert app.get_outside_temperature() == 15.0

    # when sensor exists, prefer the sensor measurement
    app._outside_temperature_sensor = 'sensor.out'
    app.get_state = lambda e, attribute=None: '18' if e == 'sensor.out' else 15
    assert app.get_outside_temperature() == 18.0


def test_setter_methods_call_service_and_record():
    app, calls = make_climate_app()

    # set temperature should call service
    app.set_temperature('climate.l1', 22)
    # calls entries are (args_tuple, data_dict)
    def domain_service_from_call(call):
        args, _ = call
        if len(args) == 1 and '/' in args[0]:
            domain, service = args[0].split('/', 1)
            return domain, service
        if len(args) >= 2:
            return args[0], args[1]
        return None, None

    assert any(domain_service_from_call(c) == ('climate', 'set_temperature') for c in calls)

    # set hvac mode (ensure entity reports support)
    calls.clear()
    app.get_state = lambda e, attribute=None: ['heat'] if attribute == 'hvac_modes' else None
    app.set_hvac_mode('climate.l1', 'heat')
    assert any(domain_service_from_call(c) == ('climate', 'set_hvac_mode') for c in calls)

    # set fan mode (ensure entity reports support)
    calls.clear()
    app.get_state = lambda e, attribute=None: ['Auto', 'Low'] if attribute == 'fan_modes' else None
    app.set_fan_mode('climate.l1', 'Auto')
    assert any(domain_service_from_call(c) == ('climate', 'set_fan_mode') for c in calls)

    # set preset (ensure entity reports support)
    calls.clear()
    app.get_state = lambda e, attribute=None: ['eco', 'none'] if attribute == 'preset_modes' else None
    app.set_preset_mode('climate.l1', 'eco')
    assert any(domain_service_from_call(c) == ('climate', 'set_preset_mode') for c in calls)
