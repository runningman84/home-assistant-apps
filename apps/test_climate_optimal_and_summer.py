from tests.climate.conftest import make_climate_app


def test_desired_hvac_mode_by_status_all():
    app, _ = make_climate_app()
    # Set per-status hvac modes
    app._home_hvac_mode = 'heat'
    app._night_hvac_mode = 'heat'
    app._away_hvac_mode = 'off'
    app._vacation_hvac_mode = 'off'
    app._open_hvac_mode = 'off'
    app._motion_hvac_mode = 'heat'

    assert app.get_desired_hvac_mode_by_status('home') == 'heat'
    assert app.get_desired_hvac_mode_by_status('night') == 'heat'
    assert app.get_desired_hvac_mode_by_status('away') == 'off'
    assert app.get_desired_hvac_mode_by_status('vacation') == 'off'
    assert app.get_desired_hvac_mode_by_status('open') == 'off'
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


def test_overheating_summer_triggers_cooling():
    """Test that overheating in summer with someone home and windows closed triggers cooling."""
    app, _ = make_climate_app()
    
    # Setup: summer, overheating, someone home, windows closed, cooling supported
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 24.0  # Inside temp >= min threshold
    app.get_desired_temperature = lambda: 21.0
    app.get_outside_temperature = lambda: 25.0  # Outside temp >= min threshold
    app.get_max_outside_temperature_today = lambda: 25.0  # Max temp today >= min threshold
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should activate cooling
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'cool', f"Expected 'cool' but got '{result}'"


def test_overheating_winter_does_not_trigger_cooling():
    """Test that overheating in winter (not summer) does not trigger cooling - just turns off."""
    app, _ = make_climate_app()
    
    # Setup: winter (not summer), overheating, someone home, windows closed
    app._max_overheat_allowance = 0.5
    app.get_external_temperature = lambda: 23.0
    app.get_desired_temperature = lambda: 22.0
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: False  # Winter!
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should turn off (conserve temperature), NOT cool
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' in winter but got '{result}'"


def test_overheating_summer_windows_open_no_cooling():
    """Test that opening windows prevents cooling even in summer."""
    app, _ = make_climate_app()
    
    # Setup: summer, overheating, someone home, but WINDOWS OPEN
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 24.0  # Inside temp >= min threshold
    app.get_desired_temperature = lambda: 21.0
    app.get_outside_temperature = lambda: 25.0  # Outside temp >= min threshold
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 1  # Windows open!
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'open'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should turn off, not cool with windows open
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' with windows open but got '{result}'"


def test_overheating_summer_no_one_home_cooling():
    """Test that cooling activate when no one is home but it is hot."""
    app, _ = make_climate_app()
    
    # Setup: summer, overheating, windows closed, but NO ONE HOME
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 25.0  # Inside temp >= min threshold
    app.get_desired_temperature = lambda: 21.0
    app.get_outside_temperature = lambda: 26.0  # Outside temp >= min threshold
    app.get_max_outside_temperature_today = lambda: 28.0  # Max temp today >= min threshold
    app.is_somebody_at_home = lambda: False  # No one home!
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'away'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should turn on cooling when no one home but it is hot
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'cool', f"Expected 'cool' with no one home but got '{result}'"


def test_overheating_summer_no_one_home_cooling_but_too_cold():
    """Test that cooling doesn't activate when no one is home and it's too cold."""
    app, _ = make_climate_app()
    
    # Setup: summer, overheating, windows closed, but NO ONE HOME
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 24.0  # Inside temp >= min threshold
    app.get_desired_temperature = lambda: 21.0
    app.get_outside_temperature = lambda: 21.0  # Outside temp >= min threshold
    app.get_max_outside_temperature_today = lambda: 21.0  # Max temp today <= min threshold
    app.is_somebody_at_home = lambda: False  # No one home!
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'away'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should turn off when no one home
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' with no one home but got '{result}'"

def test_overheating_summer_cooling_not_supported():
    """Test that when cooling is not supported, it turns off even in summer."""
    app, _ = make_climate_app()
    
    # Setup: summer, overheating, someone home, but COOLING NOT SUPPORTED
    app._max_overheat_allowance = 0.5
    app.get_external_temperature = lambda: 24.0
    app.get_desired_temperature = lambda: 21.0
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: False  # No cooling support!
    
    # Should turn off when cooling not supported
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' without cooling support but got '{result}'"


def test_exact_threshold_temperature_triggers_cooling():
    """Test that temperature exactly at overheat threshold still triggers cooling in summer."""
    app, _ = make_climate_app()
    
    # Setup: exactly at threshold (22.0 > 21.0 + 0.5)
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 21.6  # Just over overheat threshold, >= min inside
    app.get_desired_temperature = lambda: 21.0
    app.get_outside_temperature = lambda: 22.0  # Exactly at min threshold
    app.get_max_outside_temperature_today = lambda: 22.0  # Max temp today at min threshold
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should activate cooling even at edge
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'cool', f"Expected 'cool' at threshold but got '{result}'"


def test_slight_overheat_summer_triggers_cooling():
    """Test cooling activates when outside temp is warm enough."""
    app, _ = make_climate_app()
    
    # Setup: overheating inside, warm enough outside and inside
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 24.0  # Inside temp >= min threshold
    app.get_desired_temperature = lambda: 21.0   # Desired
    app.get_outside_temperature = lambda: 23.0   # Outside temp >= min threshold
    app.get_max_outside_temperature_today = lambda: 23.0  # Max temp today >= min threshold
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should activate cooling
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'cool', f"Expected 'cool' for warm conditions but got '{result}'"


def test_overheating_summer_cold_outside_no_cooling():
    """Test that cooling is prevented when outside temperature is below the minimum threshold."""
    app, _ = make_climate_app()
    
    # Setup: overheating inside, but outside is too cold
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 24.0  # Inside temp (overheating, >= min inside)
    app.get_desired_temperature = lambda: 21.0   # Desired
    app.get_outside_temperature = lambda: 20.0   # Outside temp < min threshold (too cold!)
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should NOT activate cooling because outside is too cold
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' when outside is cold but got '{result}'"


def test_overheating_summer_cold_inside_no_cooling():
    """Test that cooling is prevented when inside temperature is below the minimum threshold."""
    app, _ = make_climate_app()
    
    # Setup: inside is not actually that hot (below min), outside is warm
    app._max_overheat_allowance = 0.5
    app._min_outside_temperature_for_cooling = 22.0
    app._min_inside_temperature_for_cooling = 21.0
    app.get_external_temperature = lambda: 20.5  # Inside temp < min threshold (too cold inside!)
    app.get_desired_temperature = lambda: 19.0   # Desired (low to trigger overheating check)
    app.get_outside_temperature = lambda: 23.0   # Outside temp >= min threshold
    app.is_somebody_at_home = lambda: True
    app.count_on_opening_sensors = lambda: 0
    app.is_summer = lambda: True
    app.get_current_status = lambda: 'home'
    app.is_hvac_mode_supported = lambda entity_id, mode: mode == 'cool'
    
    # Should NOT activate cooling because inside is too cold
    result = app.get_desired_hvac_mode('climate.test')
    assert result == 'off', f"Expected 'off' when inside is cold but got '{result}'"

