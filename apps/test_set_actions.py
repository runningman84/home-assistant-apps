

def make_app(state_map=None):
    from apps.climate import ClimateControl
    app = object.__new__(ClimateControl)
    app.args = {}
    state_map = state_map or {}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    # stubs for service calls and recording
    app.call_service = lambda *a, **k: setattr(app, '_last_call', (a, k))
    app.record_internal_change = lambda : setattr(app, '_internal_changed', True)
    app._min_temperature = 7
    app._night_start = "23:15:00"
    app._night_end = "08:30:00"
    app._holiday_sensor = None
    app._workday_sensor = None
    app._outside_temperature_sensor = None
    app._workday_tomorrow_sensor = None
    app._summer_temperature_threshold_tomorrow = 18
    app._night_start_workday = "22:15:00"
    app._night_end_workday = "06:30:00"
    return app


def test_set_temperature_and_hvac_and_fan_and_preset():
    app = make_app(state_map={'climate.l': 'on'})
    # target initially different
    app.get_state = lambda e, attribute=None: '20' if attribute == 'temperature' else '21'
    app.set_temperature('climate.l', 22)
    assert hasattr(app, '_last_call')
    assert getattr(app, '_internal_changed', False) is True

    # hvac
    app.get_state = lambda e, attribute=None: 'heat,off' if attribute == 'hvac_modes' else 'off'
    app.set_hvac_mode('climate.l', 'heat')
    assert hasattr(app, '_last_call')

    # fan
    app.get_state = lambda e, attribute=None: ['Auto', 'Low'] if attribute == 'fan_modes' else 'Low'
    app.set_fan_mode('climate.l', 'Auto')
    assert hasattr(app, '_last_call')

    # preset
    app.get_state = lambda e, attribute=None: ['quiet'] if attribute == 'preset_modes' else 'none'
    app.set_preset_mode('climate.l', 'quiet')
    assert hasattr(app, '_last_call')


def test_set_optimal_temperature_skips_fan_only_mode():
    """Test that set_optimal_temperature does not set temperature when mode is fan_only."""
    app = make_app()
    
    # Setup: mode is fan_only, temperature would be different
    app.get_desired_temperature = lambda: 21.0
    app.get_desired_hvac_mode = lambda entity_id: 'fan_only'
    app.get_target_temperature = lambda entity_id: 16.0
    app.get_desired_target_temperature = lambda entity_id: 26.5
    app.log = lambda msg, level="INFO": None  # Suppress logs
    
    # Ensure call_service is not called
    call_service_called = []
    app.call_service = lambda *a, **k: call_service_called.append((a, k))
    
    app.set_optimal_temperature('climate.test')
    
    # Should NOT call service because mode is fan_only
    assert len(call_service_called) == 0, "set_temperature should not be called when mode is fan_only"

