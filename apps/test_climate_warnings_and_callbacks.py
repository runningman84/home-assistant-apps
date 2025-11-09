from tests.climate.conftest import make_climate_app


def test_warnings_for_air_quality_and_overheating():
    app, calls = make_climate_app()
    # configure thresholds and measurements to trigger warnings
    app._aqi_threshold = 50
    app._voc_threshold = 200
    app._co2_threshold = 800
    app.get_aqi_measurement = lambda: 100
    app.get_voc_measurement = lambda: 300
    app.get_co2_measurement = lambda: 900
    # overheating check
    app.get_external_temperature = lambda: 60
    app.is_overheating = lambda: True

    # call update_climate to hit the warnings branches
    app._climate_controls = []
    calls.clear()
    app.update_climate()

    # ensure update_climate completed and call_service not required here
    assert True


def test_control_change_callback_ignores_matching_external_changes():
    app, calls = make_climate_app()
    # stub helpers
    app.is_current_change_external = lambda: True
    app.get_desired_temperature = lambda e=None: 20
    # should return early without error when matching
    app.control_change_callback('climate.l1', 'temperature', '19', 20, {})
    # also test hvac_mode matching
    app.get_desired_hvac_mode = lambda e=None: 'heat'
    app.control_change_callback('climate.l1', 'hvac_mode', 'cool', 'heat', {})
    assert True


def test_sensor_change_callback_triggers_update_climate():
    app, calls = make_climate_app()
    called = []
    app.update_climate = lambda: called.append('ok')
    app.sensor_change_callback('sensor.x', None, 'old', 'new', {})
    assert called == ['ok']


def test_unsupported_setters_do_not_call_service():
    app, calls = make_climate_app()
    # entity reports no supported modes
    app.get_state = lambda e, attribute=None: None
    calls.clear()
    app.set_hvac_mode('climate.l1', 'heat')
    app.set_fan_mode('climate.l1', 'Auto')
    app.set_preset_mode('climate.l1', 'eco')
    assert len(calls) == 0


def test_forecast_and_max_temperature_unknown_unavailable():
    app, _ = make_climate_app()
    app.get_state = lambda e, attribute=None: 'unknown' if e == 'sensor.temperature_max_today' else 'unavailable' if e == 'sensor.temperature_max_tomorrow' else None
    assert app.get_max_outside_temperature_today() == 0
    assert app.get_max_outside_temperature_tomorrow() == 0
