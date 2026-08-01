from datetime import datetime


def test_last_disarm_blocks_auto_arm(make_alarm_with_maps):
    """A recent disarm should make is_last_disarming_recent() True and block auto-arming."""
    app = make_alarm_with_maps({}, {}, {'always': {}})

    # set last disarm to now
    app._last_disarm_timestamp = datetime.now().astimezone()

    # make other predicates that would normally allow away auto-arm
    app.in_guest_mode = lambda: False
    app.in_vacation_mode = lambda: False
    app.is_somebody_at_home = lambda: False
    app.is_nobody_at_home = lambda: True

    assert app.is_last_disarming_recent() is True
    assert app.is_auto_arming_allowed() is False


def test_armed_away_threshold_lowered_by_vacuum_and_triggers(make_alarm_with_maps):
    """When vacuum is returning/cleaning the away threshold is 1 and a single sensor can trigger."""
    calls = []

    device_class_map = {'door1': 'door'}
    state_map = {'door1': 'on'}
    sensors = {'armed_away': {'group1': ['door1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # simulate returning vacuum which lowers both thresholds to 1
    app.count_returning_vacuum_cleaners = lambda: 1
    assert app.get_armed_away_sensor_threshold() == 1
    assert app.get_armed_away_sensor_categories_threshold() == 1

    app.call_alarm_control_panel = lambda action: calls.append(action)
    app.is_alarm_armed_away = lambda: True
    app._alarm_type = 'burglar'  # Set alarm type for category checking

    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls


def test_armed_away_requires_multiple_sensor_categories(make_alarm_with_maps):
    """Armed away mode requires both sensor count threshold AND category threshold to trigger burglar alarm."""
    calls = []

    # Two sensors of the same category (door)
    device_class_map = {'door1': 'door', 'door2': 'door'}
    state_map = {'door1': 'on', 'door2': 'on'}
    sensors = {'armed_away': {'group1': ['door1', 'door2']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.call_alarm_control_panel = lambda action: calls.append(action)
    app.is_alarm_armed_away = lambda: True

    # Default thresholds: 2 sensors AND 2 categories required
    assert app.get_armed_away_sensor_threshold() == 2
    assert app.get_armed_away_sensor_categories_threshold() == 2

    app.analyze_and_trigger()

    # Should NOT trigger because only 1 category (door) despite 2 sensors
    assert 'alarm_trigger' not in calls


def test_armed_away_triggers_with_multiple_categories(make_alarm_with_maps):
    """Armed away mode triggers when both sensor count AND category thresholds are met."""
    calls = []

    # Two sensors of different categories (door and motion)
    device_class_map = {'door1': 'door', 'motion1': 'motion'}
    state_map = {'door1': 'on', 'motion1': 'on'}
    sensors = {'armed_away': {'group1': ['door1', 'motion1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.call_alarm_control_panel = lambda action: calls.append(action)
    app.is_alarm_armed_away = lambda: True

    # Default thresholds: 2 sensors AND 2 categories required
    assert app.get_armed_away_sensor_threshold() == 2
    assert app.get_armed_away_sensor_categories_threshold() == 2

    app.analyze_and_trigger()

    # Should trigger because we have 2 sensors AND 2 different categories
    assert 'alarm_trigger' in calls


def test_armed_away_with_three_sensors_two_categories(make_alarm_with_maps):
    """Armed away with 3 sensors from 2 categories should trigger (both thresholds met)."""
    calls = []

    # Three sensors: 2 doors + 1 motion = 2 categories
    device_class_map = {'door1': 'door', 'door2': 'door', 'motion1': 'motion'}
    state_map = {'door1': 'on', 'door2': 'on', 'motion1': 'on'}
    sensors = {'armed_away': {'group1': ['door1', 'door2', 'motion1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.call_alarm_control_panel = lambda action: calls.append(action)
    app.is_alarm_armed_away = lambda: True

    app.analyze_and_trigger()

    # Should trigger: 3 sensors (>= 2) AND 2 categories (>= 2)
    assert 'alarm_trigger' in calls


def test_is_auto_arming_disallowed_when_auto_home_not_allowed(make_alarm_with_maps):
    """If somebody is home but auto home arming is not allowed, is_auto_arming_allowed() is False."""
    app = make_alarm_with_maps({}, {}, {'always': {}})

    app._last_disarm_timestamp = None
    app.in_guest_mode = lambda: False
    app.in_vacation_mode = lambda: False
    app.is_somebody_at_home = lambda: True
    app.is_time_in_arm_night_window = lambda: False
    app.is_nobody_at_home = lambda: False
    app.is_auto_arming_home_allowed = lambda: False

    assert app.is_auto_arming_allowed() is False


def test_check_sensor_temperature_threshold(make_alarm_with_maps):
    """Temperature sensors above threshold should make check_sensor return False."""
    device_class_map = {'sensor_temp': 'temperature'}
    state_map = {'sensor_temp': '60'}
    sensors = {'always': {'fire': ['sensor_temp']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # default fixture threshold is 50 so 60 should be considered critical
    assert app.check_sensor('sensor_temp', desired_state='off') is False

    # raise threshold so 60 is okay
    app._fire_temperature_threshold = 100
    assert app.check_sensor('sensor_temp', desired_state='off') is True


def test_check_sensor_invalid_state_is_ignored(make_alarm_with_maps):
    """Sensors in 'unknown' or 'unavailable' states are ignored by get_alerts/check_sensor."""
    device_class_map = {'sensor1': 'motion'}
    state_map = {'sensor1': 'unknown'}
    sensors = {'always': {'burglar': ['sensor1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    assert app.check_sensor('sensor1') is True
    alerts = app.get_alerts()
    assert alerts == {}


def test_check_sensor_timeout_recent_change_returns_false(make_alarm_with_maps):
    """If a sensor changed recently (last_update < timeout) check_sensor should return False even when state matches desired."""
    device_class_map = {'sensor2': 'door'}
    state_map = {'sensor2': 'off'}
    sensors = {'always': {'burglar': ['sensor2']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # simulate recent update 1s ago
    app.get_seconds_since_update = lambda e: 1.0

    assert app.check_sensor('sensor2', desired_state='off', timeout=10) is False


def test_get_alerts_with_alarm_type_filter(make_alarm_with_maps):
    """get_alerts(..., alarm_type='fire') should only return fire alerts even if other categories are active."""
    device_class_map = {'sensor_fire': 'temperature', 'door1': 'door'}
    state_map = {'sensor_fire': '80', 'door1': 'on'}
    sensors = {'always': {'fire': ['sensor_fire'], 'burglar': ['door1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    alerts_fire = app.get_alerts(alarm_type='fire')
    assert 'fire' in alerts_fire
    assert 'burglar' not in alerts_fire
