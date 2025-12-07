from datetime import datetime, timezone, timedelta


def test_check_sensor_ignored_when_currently_unavailable_within_timeout(make_alarm_with_maps):
    """If a sensor became unavailable recently (still unavailable), it should be ignored."""
    device_class_map = {'s1': 'door'}
    state_map = {'s1': 'off'}
    sensors = {'always': {'burglar': ['s1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    now = datetime.now(timezone.utc)
    # became unavailable 5 seconds ago, timeout is 10s
    app._sensors_unavailable = {'s1': {'start': now - timedelta(seconds=5), 'end': None}}

    assert app.check_sensor('s1', desired_state='off', timeout=10) is True


def test_check_sensor_ignored_when_recently_became_available(make_alarm_with_maps):
    """If a sensor was unavailable but became available within timeout, it should be ignored."""
    device_class_map = {'s2': 'door'}
    state_map = {'s2': 'off'}
    sensors = {'always': {'burglar': ['s2']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    now = datetime.now(timezone.utc)
    # unavailable period ended 5 seconds ago, timeout is 10s
    app._sensors_unavailable = {'s2': {'start': now - timedelta(seconds=20), 'end': now - timedelta(seconds=5)}}

    assert app.check_sensor('s2', desired_state='off', timeout=10) is True


def test_check_sensor_not_ignored_when_unavailability_older_than_timeout(make_alarm_with_maps):
    """If a sensor was unavailable but returned long before timeout, normal timeout logic applies."""
    device_class_map = {'s3': 'door'}
    state_map = {'s3': 'off'}
    sensors = {'always': {'burglar': ['s3']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    now = datetime.now(timezone.utc)
    # unavailable period ended 20 seconds ago, timeout is 10s
    app._sensors_unavailable = {'s3': {'start': now - timedelta(seconds=200), 'end': now - timedelta(seconds=20)}}

    # simulate a recent state change 1s ago which should trigger timeout blocking
    app.get_seconds_since_update = lambda e: 1.0

    assert app.check_sensor('s3', desired_state='off', timeout=10) is False

