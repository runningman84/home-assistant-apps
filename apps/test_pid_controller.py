"""Tests for PID controller functionality."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from tests.climate.conftest import make_climate_app


def test_pid_disabled_by_default():
    """Test that PID controller is disabled by default."""
    app, _ = make_climate_app()
    
    app._enable_pid = False
    app.get_current_status = lambda: 'home'
    
    # PID should return 0 when disabled
    offset = app.calculate_pid_offset('climate.test', 20.0, 21.0, 'heat')
    assert offset == 0.0, f"Expected 0.0, got {offset}"


def test_pid_enabled_returns_offset():
    """Test that PID controller returns non-zero offset when enabled."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    app._pid_state = {
        'climate.test': {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': None,
            'last_status': None,
            'last_hvac_mode': None
        }
    }
    app.get_current_status = lambda: 'home'
    
    # First call initializes state
    offset = app.calculate_pid_offset('climate.test', 20.0, 21.0, 'heat')
    assert offset == 0.0, f"First call should return 0.0, got {offset}"
    
    # Second call should return proportional term
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime.now(timezone.utc).astimezone() + timedelta(seconds=60)
        offset = app.calculate_pid_offset('climate.test', 20.0, 21.0, 'heat')
        # Error = 20.0 - 21.0 = -1.0
        # P term = 1.0 * -1.0 = -1.0
        # Should be negative (too cold, needs more heat)
        assert offset < 0, f"Expected negative offset, got {offset}"


def test_pid_proportional_term():
    """Test that proportional term is calculated correctly."""
    app, _ = make_climate_app()
    
    # Enable PID with only P term
    app._enable_pid = True
    app._pid_kp = 2.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 10.0
    
    entity_id = 'climate.test'
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': datetime.now(timezone.utc).astimezone() - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    app.get_current_status = lambda: 'home'
    
    # Current temp = 20.0, desired = 22.0
    # Error = 20.0 - 22.0 = -2.0
    # P term = 2.0 * -2.0 = -4.0
    offset = app.calculate_pid_offset(entity_id, 20.0, 22.0, 'heat')
    assert abs(offset - (-4.0)) < 0.01, f"Expected -4.0, got {offset}"


def test_pid_integral_accumulation():
    """Test that integral term accumulates over time."""
    app, _ = make_climate_app()
    
    # Enable PID with only I term
    app._enable_pid = True
    app._pid_kp = 0.0
    app._pid_ki = 0.1
    app._pid_kd = 0.0
    app._pid_output_limit = 10.0
    
    entity_id = 'climate.test'
    current_status = 'home'
    app.get_current_status = lambda: current_status
    
    # Initialize state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': -1.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # First call: error = -1.0 for 60 seconds
    # Integral accumulates: 0.0 + (-1.0 * 60) = -60.0
    # I term = 0.1 * -60.0 = -6.0
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time + timedelta(seconds=60)
        offset1 = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'heat')
        assert offset1 < 0, f"Expected negative offset, got {offset1}"
        
        # Second call: error still -1.0 for another 60 seconds
        # Integral: -60.0 + (-1.0 * 60) = -120.0
        # I term = 0.1 * -120.0 = -12.0
        mock_datetime.now.return_value = start_time + timedelta(seconds=120)
        offset2 = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'heat')
        
        # Second offset should be more negative (accumulated error)
        assert offset2 < offset1, f"Integral should accumulate: {offset2} should be < {offset1}"


def test_pid_derivative_term():
    """Test that derivative term responds to rate of change."""
    app, _ = make_climate_app()
    
    # Enable PID with only D term
    app._enable_pid = True
    app._pid_kp = 0.0
    app._pid_ki = 0.0
    app._pid_kd = 1.0
    app._pid_output_limit = 10.0
    
    entity_id = 'climate.test'
    current_status = 'home'
    app.get_current_status = lambda: current_status
    
    # Initialize state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': -2.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Temperature is rising (error changing from -2.0 to -1.0)
    # Error change = -1.0 - (-2.0) = 1.0 over 60 seconds
    # Derivative = 1.0 / 60 = 0.0167
    # D term = 1.0 * 0.0167 = 0.0167
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time + timedelta(seconds=60)
        offset = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'heat')
        # Should be slightly positive (temperature rising, reduce heating)
        assert offset > 0, f"Expected positive offset (temp rising), got {offset}"


def test_pid_output_limiting():
    """Test that PID output is limited to configured maximum."""
    app, _ = make_climate_app()
    
    # Enable PID with high P term
    app._enable_pid = True
    app._pid_kp = 10.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 3.0  # Limit to ±3°C
    
    entity_id = 'climate.test'
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': datetime.now(timezone.utc).astimezone() - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    app.get_current_status = lambda: 'home'
    
    # Large error: current = 15.0, desired = 25.0
    # Error = 15.0 - 25.0 = -10.0
    # P term = 10.0 * -10.0 = -100.0
    # Should be limited to -3.0
    offset = app.calculate_pid_offset(entity_id, 15.0, 25.0, 'heat')
    assert offset == -3.0, f"Expected -3.0 (limited), got {offset}"


def test_pid_anti_windup():
    """Test that integral term is limited to prevent windup."""
    app, _ = make_climate_app()
    
    # Enable PID with high I term
    app._enable_pid = True
    app._pid_kp = 0.0
    app._pid_ki = 1.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    current_status = 'home'
    app.get_current_status = lambda: current_status
    
    # Initialize state with large integral already accumulated
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 1000.0,  # Very large accumulated error
            'last_error': -10.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Add more error: current = 10.0, desired = 20.0, error = -10.0
    # Integral: 1000.0 + (-10.0 * 60) = 400.0, clamped to max_integral (5.0)
    # I term = 1.0 * 5.0 = 5.0
    # Output limited to 5.0
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time + timedelta(seconds=60)
        offset = app.calculate_pid_offset(entity_id, 10.0, 20.0, 'heat')
        
        # Output should be limited by anti-windup
        assert offset == 5.0, f"Expected 5.0 (anti-windup limited), got {offset}"
        
        # Integral should be limited too
        max_integral = app._pid_output_limit / max(app._pid_ki, 0.001)
        assert app._pid_state[entity_id]['integral'] <= max_integral, \
            f"Integral {app._pid_state[entity_id]['integral']} should be <= {max_integral}"


def test_pid_resets_on_status_change():
    """Test that PID state resets when status changes."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    current_status = 'home'
    app.get_current_status = lambda: current_status
    
    # Initialize state with accumulated integral
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 100.0,
            'last_error': -5.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Change status
    current_status = 'away'
    
    # Call PID - should reset and return 0
    offset = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'heat')
    assert offset == 0.0, f"Expected 0.0 (reset), got {offset}"
    
    # Integral should be reset
    assert app._pid_state[entity_id]['integral'] == 0.0, \
        f"Integral should be reset to 0, got {app._pid_state[entity_id]['integral']}"


def test_pid_resets_on_hvac_mode_change():
    """Test that PID state resets when HVAC mode changes."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize state with accumulated integral
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 100.0,
            'last_error': -5.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Change HVAC mode
    offset = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'cool')
    assert offset == 0.0, f"Expected 0.0 (reset), got {offset}"
    
    # Integral should be reset
    assert app._pid_state[entity_id]['integral'] == 0.0, \
        f"Integral should be reset to 0, got {app._pid_state[entity_id]['integral']}"


def test_pid_zero_time_delta():
    """Test that PID handles zero time delta gracefully."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    current_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': current_time,  # Same time
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Call with same time - should return 0
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = current_time
        offset = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'heat')
        assert offset == 0.0, f"Expected 0.0 (zero dt), got {offset}"


def test_pid_integration_with_temperature_calculation_winter_normal():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,  # Perfect temperature
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    app.get_external_temperature = lambda: 21.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 21.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 21.0, desired = 21.0, error = 0.0
    # P term = 1.0 * 0.0 = 0.0
    # Target should be 21.0 + (0.0) = 21.0
    assert target_temp == 21.0, f"PID should keep target temp at 21.0, got {target_temp}"

def test_pid_integration_with_temperature_calculation_winter_too_cold():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': -2.0,  # Too cold
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    app.get_external_temperature = lambda: 15.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 19.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 15.0, desired = 21.0, error = -2.0
    # P term = 1.0 * 5.0 = 5.0
    # Target should be 21.0 + (5.0) = 26.0
    assert target_temp == 26.0, f"PID should increase target temp to 26.0, got {target_temp}"

def test_pid_integration_with_temperature_calculation_winter_too_hot():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 2.0,  # Too hot
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: False
    app.get_desired_hvac_mode = lambda entity_id=None: 'heat'
    app.get_external_temperature = lambda: 25.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 25.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 25.0, desired = 21.0, error = 4.0
    # P term = 1.0 * 0.0 = 0.0
    # Target should be 21.0 + (-5.0) = 17.0
    assert target_temp < 21.0, f"PID should decrease target temp, got {target_temp}"

def test_pid_integration_with_temperature_calculation_summer_normal():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._cooling_temperature = 22.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,  # Too cold
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'cool'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    app.get_external_temperature = lambda: 22.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 22.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 22.0, desired = 22.0, error = 0.0
    # P term = 1.0 * 0.0 = 0.0
    # Target should be 22.0 + (0.0) = 22.0
    assert target_temp == 22.0, f"PID should keep target temp at 22.0, got {target_temp}"

def test_pid_integration_with_temperature_calculation_summer_too_cold():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._cooling_temperature = 22.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': -2.0,  # Too cold
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'cool'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    app.get_external_temperature = lambda: 15.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 19.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 15.0, desired = 22.0, error = -2.0
    # P term = 1.0 * 5.0 = 5.0
    # Target should be 22.0 + (5.0) = 27.0
    assert target_temp == 27.0, f"PID should increase target temp to 27.0, got {target_temp}"

def test_pid_integration_with_temperature_calculation_summer_too_hot():
    """Test that PID offset is applied to target temperature."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app._climate_controls = [entity_id]
    app._home_temperature = 21.0
    app._offset_temperature_heating = 0.0
    app._offset_temperature_cooling = 0.0
    app._overdrive_mode = False
    
    # Initialize PID state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 2.0,  # Too hot
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'cool'
        }
    }
    
    # Mock methods
    app.get_current_status = lambda: 'home'
    app.is_summer = lambda: True
    app.get_desired_hvac_mode = lambda entity_id=None: 'cool'
    app.get_external_temperature = lambda: 25.0
    
    # Mock get_state to return current temperature (inaccurate for testing PID only external temperature is used)
    app.get_state = lambda e, attribute=None: 25.0 if attribute == 'current_temperature' else None
    
    # Get target temperature (should include PID offset)
    target_temp = app.get_desired_target_temperature(entity_id)
    
    # Current = 25.0, desired = 21.0, error = 4.0
    # P term = 1.0 * 0.0 = 0.0
    # Target should be 21.0 + (-5.0) = 17.0
    assert target_temp < 21.0, f"PID should decrease target temp, got {target_temp}"

def test_pid_with_cooling_mode():
    """Test that PID works correctly in cooling mode."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'cool'
        }
    }
    
    # Current temp = 26.0, desired = 24.0
    # Error = 26.0 - 24.0 = 2.0 (too hot)
    # P term = 1.0 * 2.0 = 2.0
    # In cooling mode, positive error means too hot, so positive offset lowers cooling target
    offset = app.calculate_pid_offset(entity_id, 26.0, 24.0, 'cool')
    assert offset > 0, f"Expected positive offset (too hot), got {offset}"
    assert abs(offset - 2.0) < 0.01, f"Expected 2.0, got {offset}"


def test_pid_missing_entity_state():
    """Test that PID returns 0 if entity not in state dict."""
    app, _ = make_climate_app()
    
    # Enable PID but don't initialize state for entity
    app._enable_pid = True
    app._pid_state = {}
    
    app.get_current_status = lambda: 'home'
    
    # Should return 0 (no state for entity)
    offset = app.calculate_pid_offset('climate.unknown', 20.0, 21.0, 'heat')
    assert offset == 0.0, f"Expected 0.0 (no state), got {offset}"


def test_pid_combined_terms():
    """Test that all PID terms work together correctly."""
    app, _ = make_climate_app()
    
    # Enable PID with all terms
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 10.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize state
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': -1.5,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Current = 19.0, desired = 21.0
    # Error = 19.0 - 21.0 = -2.0
    # P term = 1.0 * -2.0 = -2.0
    # I term = 0.1 * (0.0 + -2.0 * 60) = 0.1 * -120.0 = -12.0
    # D term = 0.05 * ((-2.0 - -1.5) / 60) = 0.05 * (-0.5 / 60) = -0.000417
    # Total = -2.0 + -12.0 + -0.000417 = -14.000417
    # Limited to -10.0
    with patch('apps.climate.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time + timedelta(seconds=60)
        offset = app.calculate_pid_offset(entity_id, 19.0, 21.0, 'heat')
        
        # Should be limited to -10.0
        assert offset == -10.0, f"Expected -10.0 (limited), got {offset}"


def test_pid_positive_and_negative_errors():
    """Test that PID handles both positive and negative errors."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.0
    app._pid_kd = 0.0
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    start_time = datetime.now(timezone.utc).astimezone()
    
    # Test negative error (too cold)
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': start_time - timedelta(seconds=60),
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    offset_cold = app.calculate_pid_offset(entity_id, 18.0, 21.0, 'heat')
    assert offset_cold < 0, f"Too cold should give negative offset, got {offset_cold}"
    
    # Test positive error (too hot)
    app._pid_state[entity_id]['last_error'] = 0.0
    app._pid_state[entity_id]['last_time'] = start_time - timedelta(seconds=60)
    
    offset_hot = app.calculate_pid_offset(entity_id, 24.0, 21.0, 'heat')
    assert offset_hot > 0, f"Too hot should give positive offset, got {offset_hot}"


def test_pid_resets_on_off_mode():
    """Test that PID state resets when HVAC mode is 'off'."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize state with accumulated integral
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 50.0,
            'last_error': -3.0,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'heat'
        }
    }
    
    # Call PID with 'off' mode - should reset and return 0
    offset = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'off')
    assert offset == 0.0, f"Expected 0.0 (off mode), got {offset}"
    
    # State should be reset
    assert app._pid_state[entity_id]['integral'] == 0.0, \
        f"Integral should be reset to 0, got {app._pid_state[entity_id]['integral']}"
    assert app._pid_state[entity_id]['last_error'] == 0.0, \
        f"Last error should be reset to 0, got {app._pid_state[entity_id]['last_error']}"
    assert app._pid_state[entity_id]['last_time'] is None, \
        f"Last time should be reset to None, got {app._pid_state[entity_id]['last_time']}"


def test_pid_resets_on_fan_only_mode():
    """Test that PID state resets when HVAC mode is 'fan_only'."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize state with accumulated integral
    start_time = datetime.now(timezone.utc).astimezone()
    app._pid_state = {
        entity_id: {
            'integral': 75.0,
            'last_error': -2.5,
            'last_time': start_time,
            'last_status': 'home',
            'last_hvac_mode': 'cool'
        }
    }
    
    # Call PID with 'fan_only' mode - should reset and return 0
    offset = app.calculate_pid_offset(entity_id, 22.0, 24.0, 'fan_only')
    assert offset == 0.0, f"Expected 0.0 (fan_only mode), got {offset}"
    
    # State should be reset
    assert app._pid_state[entity_id]['integral'] == 0.0, \
        f"Integral should be reset to 0, got {app._pid_state[entity_id]['integral']}"
    assert app._pid_state[entity_id]['last_error'] == 0.0, \
        f"Last error should be reset to 0, got {app._pid_state[entity_id]['last_error']}"
    assert app._pid_state[entity_id]['last_time'] is None, \
        f"Last time should be reset to None, got {app._pid_state[entity_id]['last_time']}"


def test_pid_stays_reset_in_off_mode():
    """Test that PID stays at 0 when called multiple times in 'off' mode."""
    app, _ = make_climate_app()
    
    # Enable PID
    app._enable_pid = True
    app._pid_kp = 1.0
    app._pid_ki = 0.1
    app._pid_kd = 0.05
    app._pid_output_limit = 5.0
    
    entity_id = 'climate.test'
    app.get_current_status = lambda: 'home'
    
    # Initialize clean state
    app._pid_state = {
        entity_id: {
            'integral': 0.0,
            'last_error': 0.0,
            'last_time': None,
            'last_status': None,
            'last_hvac_mode': None
        }
    }
    
    # Call PID multiple times in 'off' mode
    offset1 = app.calculate_pid_offset(entity_id, 20.0, 21.0, 'off')
    offset2 = app.calculate_pid_offset(entity_id, 19.0, 21.0, 'off')
    offset3 = app.calculate_pid_offset(entity_id, 18.0, 21.0, 'off')
    
    # All should return 0
    assert offset1 == 0.0, f"Expected 0.0, got {offset1}"
    assert offset2 == 0.0, f"Expected 0.0, got {offset2}"
    assert offset3 == 0.0, f"Expected 0.0, got {offset3}"
    
    # State should remain reset
    assert app._pid_state[entity_id]['integral'] == 0.0, \
        f"Integral should stay 0, got {app._pid_state[entity_id]['integral']}"

