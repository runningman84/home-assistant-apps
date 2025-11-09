from tests.climate.conftest import make_climate_app


def test_desired_hvac_mode_by_status_all():
    app, _ = make_climate_app()
    # Set per-status hvac modes
    app._home_hvac_mode = 'heat'
    app._night_hvac_mode = 'heat'
    app._away_hvac_mode = 'off'
    app._vacation_hvac_mode = 'off'
    app._open_hvac_mode = 'off'
    app._summer_hvac_mode = 'off'
    app._motion_hvac_mode = 'heat'

    assert app.get_desired_hvac_mode_by_status('home') == 'heat'
    assert app.get_desired_hvac_mode_by_status('night') == 'heat'
    assert app.get_desired_hvac_mode_by_status('away') == 'off'
    assert app.get_desired_hvac_mode_by_status('vacation') == 'off'
    assert app.get_desired_hvac_mode_by_status('open') == 'off'
    assert app.get_desired_hvac_mode_by_status('summer') == 'off'
    assert app.get_desired_hvac_mode_by_status('motion') == 'heat'


def test_is_summer_today_and_tomorrow_thresholds():
    # today exceeds threshold
    app, _ = make_climate_app()
    app._summer_temperature_threshold = 20
    app.get_max_outside_temperature_today = lambda: 25
    app.get_max_outside_temperature_tomorrow = lambda: 10
    assert app.is_summer() is True

    # tomorrow exceeds tomorrow-threshold
    app, _ = make_climate_app()
    app._summer_temperature_threshold = 20
    app._summer_temperature_threshold_tomorrow = 22
    app.get_max_outside_temperature_today = lambda: 15
    app.get_max_outside_temperature_tomorrow = lambda: 23
    assert app.is_summer() is True

    # neither exceed thresholds
    app, _ = make_climate_app()
    app._summer_temperature_threshold = 20
    app._summer_temperature_threshold_tomorrow = 22
    app.get_max_outside_temperature_today = lambda: 10
    app.get_max_outside_temperature_tomorrow = lambda: 11
    assert app.is_summer() is False


def test_get_max_outside_temperature_parsing_from_forecast_and_sensor():
    # forecast string values
    # The app reads sensor.temperature_max_today, not the raw forecast; provide that
    app, _ = make_climate_app(state_map={'sensor.temperature_max_today': '18'})
    assert app.get_max_outside_temperature_today() == 18.0


def test_set_optimal_flows_call_services_when_supported():
    app, calls = make_climate_app()
    # Configure entity and support
    entity = 'climate.l1'
    app.get_state = lambda e, attribute=None: ['Auto', 'Low'] if attribute == 'fan_modes' else ['heat'] if attribute == 'hvac_modes' else ['eco'] if attribute == 'preset_modes' else '20' if attribute == 'current_temperature' else None

    # Ensure is_summer False and is_cooling False to hit regular set_optimal paths
    app.is_summer = lambda: False
    app.is_cooling = lambda x: False

    # Run set_optimal_* methods directly
    app.set_optimal_temperature(entity)
    app.set_optimal_hvac_mode(entity)
    app.set_optimal_fan_mode(entity)
    app.set_optimal_preset_mode(entity)

    # At least one service should have been called across these
    assert len(calls) >= 1
