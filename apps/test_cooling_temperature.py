"""Tests for cooling temperature logic and cooling_temperature feature."""
from tests.climate.conftest import make_climate_app


def test_cooling_temperature_used_in_cool_mode():
    """Test that cooling_temperature is used when HVAC mode is 'cool'."""
    app, _ = make_climate_app()
    
    # Set up normal heating temp and cooling temp
    app._home_temperature = 21.0
    app._cooling_temperature = 26.0
    app._home_temperature_cooling = 26.0
    
    # Mock status, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling temps to be used
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # In cool mode, should use cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 26.0, f"Expected 26.0, got {target_temp}"


def test_heating_temperature_used_in_heat_mode():
    """Test that normal temperature is used when HVAC mode is 'heat'."""
    app, _ = make_climate_app()
    
    # Set up normal heating temp and cooling temp
    app._home_temperature = 21.0
    app._cooling_temperature = 26.0
    
    # Mock status and desired hvac mode (not summer = heating mode)
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False  # Not summer, so use heating temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    
    # In heat mode, should use normal home_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 21.0, f"Expected 21.0, got {target_temp}"


def test_vacation_cooling_uses_cooling_temperature():
    """Test that vacation mode uses cooling_temperature when cooling."""
    app, _ = make_climate_app()
    
    # Set up vacation temps
    app._vacation_temperature = 15.0  # Low for heating
    app._cooling_temperature = 28.0  # High for minimal cooling
    app._vacation_temperature_cooling = 28.0
    
    # Mock vacation status, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'vacation'
    app.is_summer = lambda: True  # Must be summer for cooling temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use cooling_temperature, NOT vacation_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 28.0, f"Expected 28.0, got {target_temp}"


def test_overdrive_heating_overrides_normal_temp():
    """Test that overdrive_heating_temperature is used in heat mode with overdrive."""
    app, _ = make_climate_app()
    
    # Enable overdrive
    app._overdrive_mode = True
    app._overdrive_heating_temperature = 30.0
    app._home_temperature = 21.0
    
    # Mock status, external temp and desired hvac mode
    app.get_current_status = lambda: 'home'
    app.get_external_temperature = lambda: 18.0  # Cold, needs heating
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    
    # Should use overdrive_heating_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 30.0, f"Expected 30.0, got {target_temp}"


def test_overdrive_cooling_overrides_cooling_temp():
    """Test that overdrive_cooling_temperature is used in cool mode with overdrive."""
    app, _ = make_climate_app()
    
    # Enable overdrive
    app._overdrive_mode = True
    app._overdrive_cooling_temperature = 16.0
    app._cooling_temperature = 26.0
    
    # Mock status, external temp, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'home'
    app.get_external_temperature = lambda: 30.0  # Hot, needs cooling
    app.is_summer = lambda: True  # Must be summer for cooling
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use overdrive_cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 16.0, f"Expected 16.0, got {target_temp}"


def test_away_mode_cooling():
    """Test that away mode uses cooling_temperature when cooling."""
    app, _ = make_climate_app()
    
    # Set up away mode
    app._away_temperature = 17.0  # Low for heating
    app._cooling_temperature = 27.0
    app._away_temperature_cooling = 27.0
    
    # Mock away status, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'away'
    app.is_summer = lambda: True  # Must be summer for cooling temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 27.0, f"Expected 27.0, got {target_temp}"


def test_night_mode_cooling():
    """Test that night mode uses cooling_temperature when cooling."""
    app, _ = make_climate_app()
    
    # Set up night mode
    app._night_temperature = 18.0  # Low for heating
    app._cooling_temperature = 25.0
    app._night_temperature_cooling = 25.0
    
    # Mock night status, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'night'
    app.is_summer = lambda: True  # Must be summer for cooling temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 25.0, f"Expected 25.0, got {target_temp}"


def test_off_mode_uses_normal_temperature():
    """Test that 'off' mode uses normal temperature (not cooling temp)."""
    app, _ = make_climate_app()
    
    # Set up off mode
    app._home_temperature = 21.0
    app._cooling_temperature = 26.0
    
    # Mock status and desired hvac mode (not summer = heating temps)
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False  # Not summer, so use heating temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'off'
    
    # Off mode should use normal temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 21.0, f"Expected 21.0, got {target_temp}"


def test_fan_only_mode_uses_normal_temperature():
    """Test that 'fan_only' mode uses normal temperature (not cooling temp)."""
    app, _ = make_climate_app()
    
    # Set up fan_only mode
    app._home_temperature = 21.0
    app._cooling_temperature = 26.0
    
    # Mock status and desired hvac mode (not summer = heating temps)
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False  # Not summer, so use heating temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'fan_only'
    
    # fan_only mode should use normal temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 21.0, f"Expected 21.0, got {target_temp}"


def test_cooling_without_overdrive():
    """Test that cooling works correctly when overdrive is disabled."""
    app, _ = make_climate_app()
    
    # Disable overdrive
    app._overdrive_mode = False
    app._cooling_temperature = 24.0
    app._home_temperature_cooling = 24.0
    
    # Mock status, summer detection, and desired hvac mode
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 24.0, f"Expected 24.0, got {target_temp}"


def test_cooling_temperature_default_value():
    """Test that cooling_temperature has sensible default."""
    app, _ = make_climate_app()
    
    # Should default to 22°C (as specified in climate.py)
    assert app._cooling_temperature == 22.0


def test_offset_temperature_heating_applied():
    """Test that offset_temperature_heating is applied in heating mode."""
    app, _ = make_climate_app()
    
    app._home_temperature = 21.0
    app._offset_temperature_heating = -2.0
    app._offset_temperature_cooling = 1.0
    
    app.get_current_status = lambda: 'home'
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    
    # Should use home_temperature (21) + heating offset (-2) = 19
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 19.0, f"Expected 19.0, got {target_temp}"


def test_offset_temperature_cooling_applied():
    """Test that offset_temperature_cooling is applied in cooling mode."""
    app, _ = make_climate_app()
    
    app._cooling_temperature = 26.0
    app._home_temperature_cooling = 26.0
    app._offset_temperature_heating = -2.0
    app._offset_temperature_cooling = 1.0
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling temps
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use cooling_temperature (26) + cooling offset (1) = 27
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 27.0, f"Expected 27.0, got {target_temp}"


def test_separate_offsets():
    """Test that separate offsets work for heating and cooling."""
    app, _ = make_climate_app(args={
        'offset_temperature_heating': -2.0,
        'offset_temperature_cooling': 1.0
    })
    
    # Verify separate offsets are set
    assert app._offset_temperature_heating == -2.0
    assert app._offset_temperature_cooling == 1.0


def test_separate_min_max_for_heating_and_cooling():
    """Test that separate min/max bounds work for heating and cooling."""
    app, _ = make_climate_app(args={
        'min_temperature_heating': 5,
        'max_temperature_heating': 28,
        'min_temperature_cooling': 18,
        'max_temperature_cooling': 30
    })
    
    # Verify separate bounds are set
    assert app._min_temperature_heating == 5.0
    assert app._max_temperature_heating == 28.0
    assert app._min_temperature_cooling == 18.0
    assert app._max_temperature_cooling == 30.0


def test_cooling_respects_cooling_bounds():
    """Test that cooling mode uses cooling-specific min/max bounds."""
    app, _ = make_climate_app()
    
    # Set different bounds for cooling
    app._min_temperature_cooling = 18.0
    app._max_temperature_cooling = 28.0
    app._cooling_temperature = 15.0  # Below min
    app._home_temperature_cooling = 15.0
    app._offset_temperature_cooling = 0
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should clamp to min_temperature_cooling (18)
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 18.0, f"Expected 18.0, got {target_temp}"


def test_heating_respects_heating_bounds():
    """Test that heating mode uses heating-specific min/max bounds."""
    app, _ = make_climate_app()
    
    # Set different bounds for heating
    app._min_temperature_heating = 7.0
    app._max_temperature_heating = 25.0
    app._home_temperature = 30.0  # Above max
    app._offset_temperature_heating = 0
    
    app.get_current_status = lambda: 'home'
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    
    # Should clamp to max_temperature_heating (25)
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 25.0, f"Expected 25.0, got {target_temp}"




def test_cooling_temperature_control_overrides_static_value():
    """Test that cooling_temperature_control entity overrides static cooling_temperature."""
    state_map = {
        'input_number.cooling_temp': '24.5'
    }
    app, _ = make_climate_app(state_map=state_map)
    
    # Set up cooling control
    app._cooling_temperature = 22.0  # Static value
    app._home_temperature_cooling = 22.0
    app._home_temperature_control_cooling = 'input_number.cooling_temp'  # Control entity
    app._offset_temperature_cooling = 0
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use value from control entity (24.5), not static value (22.0)
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 24.5, f"Expected 24.5 from control entity, got {target_temp}"


def test_cooling_temperature_control_none_uses_static():
    """Test that when cooling_temperature_control is None, static value is used."""
    app, _ = make_climate_app()
    
    # No control entity
    app._cooling_temperature = 23.0
    app._home_temperature_cooling = 23.0
    app._cooling_temperature_control = None
    app._home_temperature_control_cooling = None
    app._offset_temperature_cooling = 0
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use static cooling_temperature
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 23.0, f"Expected 23.0 from static value, got {target_temp}"


def test_cooling_temperature_control_with_offset():
    """Test that cooling_temperature_control works with offset_temperature_cooling."""
    state_map = {
        'input_number.cooling_temp': '25.0'
    }
    app, _ = make_climate_app(state_map=state_map)
    
    # Set up cooling control with offset
    app._home_temperature_control_cooling = 'input_number.cooling_temp'
    app._offset_temperature_cooling = -1.5  # Sensor reads high
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Must be summer for cooling
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    
    # Should use control value (25.0) + offset (-1.5) = 23.5
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 23.5, f"Expected 23.5 (25.0 - 1.5), got {target_temp}"


def test_cooling_offset_used_when_hvac_off_in_summer():
    """Test that cooling offset is applied even when HVAC mode is 'off' during summer.
    
    This ensures the correct offset is used based on season (is_summer()) rather than
    the current HVAC mode. Fixes issue where heating offset was applied during summer
    when HVAC was off, causing incorrect temperature calculations.
    """
    app, _ = make_climate_app()
    
    # Set up temperatures and offsets
    app._home_temperature = 21.0
    app._home_temperature_cooling = 22.0
    app._offset_temperature_heating = 6.0  # Large heating offset
    app._offset_temperature_cooling = -6.0  # Large cooling offset
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True  # Summer season
    app.get_desired_hvac_mode = lambda entity_id=None: 'off'  # HVAC is off
    
    # Even though HVAC is 'off', should use cooling offset because it's summer
    # Expected: 22.0 (cooling temp) + (-6.0) (cooling offset) = 16.0
    # NOT: 22.0 + 6.0 (heating offset) = 28.0 (bug)
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 16.0, f"Expected 16.0 (cooling offset in summer), got {target_temp}"


def test_heating_offset_used_when_hvac_off_in_winter():
    """Test that heating offset is applied when HVAC mode is 'off' during winter."""
    app, _ = make_climate_app()
    
    # Set up temperatures and offsets
    app._home_temperature = 21.0
    app._offset_temperature_heating = 2.0  # Heating offset
    app._offset_temperature_cooling = -2.0  # Cooling offset
    
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False  # Winter season
    app.get_desired_hvac_mode = lambda entity_id=None: 'off'  # HVAC is off
    
    # Should use heating offset because it's winter
    # Expected: 21.0 + 2.0 = 23.0
    target_temp = app.get_desired_target_temperature()
    assert target_temp == 23.0, f"Expected 23.0 (heating offset in winter), got {target_temp}"

