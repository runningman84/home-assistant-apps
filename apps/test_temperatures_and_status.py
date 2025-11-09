

def make_app(args=None, state_map=None):
    from apps.climate import ClimateControl
    app = object.__new__(ClimateControl)
    app.args = args or {}
    state_map = state_map or {}
    app.get_state = lambda e, attribute=None: state_map.get(e)
    # defaults
    app._opening_sensors = []
    app._motion_sensors = []
    app._device_trackers = []
    app._vacation_control = None
    app._guest_control = None
    app._night_start = "23:15:00"
    app._night_end = "08:30:00"
    app._min_temperature = 7
    app._offset_temperature = 0
    app._home_temperature = 20
    app._home_temperature_control = None
    app._night_temperature = 18
    app._night_temperature_control = None
    app._away_temperature = 16
    app._away_temperature_control = None
    app._vacation_temperature = 15
    app._open_temperature = 13
    app._motion_temperature = 19
    app._summer_temperature_threshold = 15
    app._holiday_sensor = None
    app._workday_sensor = None
    app._outside_temperature_sensor = None
    app._workday_tomorrow_sensor = None
    app._summer_temperature_threshold_tomorrow = app._summer_temperature_threshold + 3
    app._night_start_workday = "22:15:00"
    app._night_end_workday = "06:30:00"
    # ensure device trackers and guest control defaults exist for get_current_status
    if not hasattr(app, '_guest_control'):
        app._guest_control = None
    if not hasattr(app, '_device_trackers'):
        app._device_trackers = []
    return app


def test_get_desired_temperature_by_status_and_minimum():
    app = make_app()
    # no controls -> should return configured defaults
    assert app.get_desired_temperature_by_status('home') == 20.0
    assert app.get_desired_temperature_by_status('night') == 18.0

    # if desired < min -> get_desired_temperature returns min
    app._min_temperature = 21
    assert app.get_desired_temperature() == 21


def test_get_current_and_target_temperature_helpers():
    app = make_app(state_map={'climate.l1': 'on'})
    app.get_state = lambda e, attribute=None: 'unavailable' if attribute == 'current_temperature' else '21'
    assert app.get_current_temperature('climate.l1') == 0
    app.get_state = lambda e, attribute=None: '20' if attribute == 'current_temperature' else '22'
    assert app.get_current_temperature('climate.l1') == 20.0
    assert app.get_target_temperature('climate.l1') == 22.0


def test_get_current_status_variations():
    # summer takes precedence
    app = make_app()
    app.get_outside_temperature = lambda: 30
    assert app.get_current_status() == 'summer'

    # open window
    app = make_app()
    app._opening_sensors = ['b']
    app.get_state = lambda e, attribute=None: 'on' if e == 'b' else None
    assert app.get_current_status() == 'open'

    # vacation
    app = make_app()
    app._vacation_control = 'vac'
    app.get_state = lambda e, attribute=None: 'on' if e == 'vac' else None
    assert app.get_current_status() == 'vacation'

    # night window
    app = make_app()
    app.is_time_in_night_window = lambda: True
    assert app.get_current_status() == 'night'

    # guest mode
    app = make_app()
    app._guest_control = 'guest'
    app.get_state = lambda e, attribute=None: 'on' if e == 'guest' else None
    assert app.get_current_status() == 'home'

    # nobody home
    app = make_app()
    app._device_trackers = ['t1']
    app.get_state = lambda e, attribute=None: 'not_home' if e == 't1' else None
    assert app.get_current_status() == 'away'

    # motion
    app = make_app()
    app._motion_sensors = ['m1']
    app.get_state = lambda e, attribute=None: 'on' if e == 'm1' else 'home' if e == 't1' else None
    app._device_trackers = ['t1']
    assert app.get_current_status() == 'motion'

    # fallback home
    app = make_app()
    # ensure at least one device tracker present and at home
    app._device_trackers = ['t1']
    app.get_state = lambda e, attribute=None: 'home' if e == 't1' else None
    assert app.get_current_status() == 'home'
