from tests.base.factories import make_base_app


def test_counting_helpers_and_last_motion_and_opening():
    app = make_base_app()

    assert app.count_opening_sensors() == 2
    # our get_seconds_since_update stub returns a recent timestamp (5s),
    # so sensors are counted as recent when filtering by state
    assert app.count_on_opening_sensors() == 2
    assert app.count_motion_sensors() == 1
    assert app.get_last_motion() == 5


def test_get_seconds_since_update_parsing_and_logging():
    app = make_base_app()

    secs = app.get_seconds_since_update("binary_sensor.door1")
    assert secs is not None and secs <= 10


def test_media_and_illumination_counting():
    app = make_base_app()
    app._media_players = ['media.player.a', 'media.player.b']

    def get_state_media(entity, attribute=None):
        if attribute == 'source':
            return 'spotify' if entity == 'media.player.a' else 'radio'
        if entity == 'media.player.a':
            return 'playing'
        return 'off'

    app.get_state = get_state_media
    # without sources -> count playing media players = 1
    assert app.count_playing_media_players() == 1
    # with sources that include spotify
    assert app.count_media_players('playing', sources=['spotify']) == 1

    # Illumination tests
    app._illumination_sensors = ['sensor.il1']
    app._min_illumination = 50
    app._max_illumination = 200
    app.get_state = lambda entity, attribute=None: 'unknown' if entity == 'sensor.il1' else None
    assert app.below_min_illumination() is True
    app.get_state = lambda entity, attribute=None: '100' if entity == 'sensor.il1' else None
    assert app.above_max_illumination() is False


def test_counts_lights_vacuums_trackers_awake_and_presence_variants():
    app = make_base_app()
    app._lights = ['light.a', 'light.b']
    app._vacuum_cleaners = ['vac.a']
    app._device_trackers = ['device.t1']
    app._awake_sensors = ['sensor.aw1']

    def get_state(entity, attribute=None):
        if entity == 'light.a':
            return 'on'
        if entity == 'light.b':
            return 'off'
        if entity == 'vac.a':
            return 'docked'
        if entity == 'device.t1':
            return 'home'
        if entity == 'sensor.aw1':
            return 'on'
        return None

    app.get_state = get_state

    assert app.count_on_lights() == 1
    assert app.count_off_lights() == 1
    assert app.count_cleaning_vacuum_cleaners() == 0
    assert app.count_docked_vacuum_cleaners() == 1
    assert app.count_home_device_trackers() == 1
    assert app.is_somebody_awake() is True
    assert app.is_nobody_awake() is False


def test_alarm_and_alarm_state_helpers():
    app = make_base_app()
    app._alarm_control_panel = 'alarm.home'

    def get_state(entity, attribute=None):
        if entity == 'alarm.home':
            return 'armed_home'
        return None

    app.get_state = get_state
    assert app.is_alarm_armed_home() is True
    assert app.is_alarm_armed() is True
    assert app.get_alarm_state() == 'armed_home'

    # when no alarm configured
    app._alarm_control_panel = None
    assert app.is_alarm_in_state('disarmed') is False
    assert app.get_alarm_state() is None
