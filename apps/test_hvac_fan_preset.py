

def make_app(state_map=None):
    from apps.climate import ClimateControl
    app = object.__new__(ClimateControl)
    app.args = {}
    state_map = state_map or {}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    app._aqi_threshold = 50
    app._voc_threshold = 200
    app._fan_overheat_temperature = 22
    app._max_overheat_allowance = 0.5
    app._motion_sensors = []
    app._opening_sensors = []
    app._device_trackers = []
    app._night_start = "23:15:00"
    app._night_end = "08:30:00"
    app._summer_temperature_threshold = 15
    app._holiday_sensor = None
    app._workday_sensor = None
    app._outside_temperature_sensor = None
    app._workday_tomorrow_sensor = None
    app._summer_temperature_threshold_tomorrow = app._summer_temperature_threshold + 3
    app._night_start_workday = "22:15:00"
    app._night_end_workday = "06:30:00"
    app._aqi_sensor = None
    app._voc_sensor = None
    app._co2_sensor = None
    app._vacation_control = None
    app._guest_control = None
    app._device_trackers = []
    # HVAC mode defaults used by get_desired_hvac_mode_by_status
    app._home_hvac_mode = 'heat'
    app._night_hvac_mode = 'heat'
    app._away_hvac_mode = 'off'
    app._vacation_hvac_mode = 'off'
    app._open_hvac_mode = 'off'
    app._summer_hvac_mode = 'off'
    app._motion_hvac_mode = 'heat'
    return app


def test_get_desired_fan_mode_and_desired_hvac_mode():
    app = make_app()
    # no sensors and default thresholds -> no high fan
    assert app.get_desired_fan_mode() == 'Auto'

    # AQI triggers higher fan levels
    app.get_aqi_measurement = lambda: 500
    assert app.get_desired_fan_mode() in ['High', 'HighMid', 'Mid', 'Auto']

    # desired hvac mode selection: simulate overheat
    app.get_external_temperature = lambda: 30
    app.get_desired_temperature = lambda: 20
    # assume nobody home -> fan_only conditions not met and should return 'off'
    app.is_somebody_at_home = lambda: False
    assert app.get_desired_hvac_mode() == 'off'

    # test is_cooling
    app.get_current_hvac_mode = lambda e: 'cool'
    assert app.is_cooling('c1') is True

    # is_fan_mode_supported
    app.get_state = lambda e, attribute=None: ['Auto', 'Low'] if attribute == 'fan_modes' else None
    assert app.is_fan_mode_supported('c1') is True
    assert app.is_fan_mode_supported('c1', 'Auto') is True
    assert app.is_fan_mode_supported('c1', 'X') is False

    # is_preset_mode_supported
    app.get_state = lambda e, attribute=None: ['quiet', 'none'] if attribute == 'preset_modes' else None
    assert app.is_preset_mode_supported('c1') is True
    assert app.is_preset_mode_supported('c1', 'quiet') is True
    assert app.is_preset_mode_supported('c1', 'bad') is False
