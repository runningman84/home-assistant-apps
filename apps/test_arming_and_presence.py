def test_motion_burglar_ignored_when_vacuum_cleaning(make_alarm_with_maps):
    """If a vacuum cleaner is cleaning, motion sensors should be ignored for burglar alerts."""
    calls = []

    device_class_map = {'motion1': 'motion'}
    state_map = {'motion1': 'on'}
    sensors = {'armed_away': {'group1': ['motion1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # report that a vacuum is currently cleaning
    app.count_cleaning_vacuum_cleaners = lambda: 1
    app.count_returning_vacuum_cleaners = lambda: 0

    # default to armed away for burglar checks
    app.is_alarm_armed_away = lambda: True

    app.call_alarm_control_panel = lambda action: calls.append(action)

    app.analyze_and_trigger()

    # no alarm should have been triggered because vacuum is cleaning
    assert 'alarm_trigger' not in calls


def test_motion_burglar_triggers_when_vacuum_docked(make_alarm_with_maps):
    """When vacuum cleaners are docked (not cleaning/returning), motion should trigger burglar alerts."""
    calls = []

    device_class_map = {'motion2': 'motion'}
    state_map = {'motion2': 'on'}
    sensors = {'armed_away': {'group1': ['motion2']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # vacuums are docked (count_cleaning and count_returning = 0 by default)
    app.count_cleaning_vacuum_cleaners = lambda: 0
    app.count_returning_vacuum_cleaners = lambda: 0

    # ensure threshold allows single-sensor trigger for this test
    app._armed_away_sensor_threshold = 1

    app.is_alarm_armed_away = lambda: True

    app.call_alarm_control_panel = lambda action: calls.append(action)

    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls


def test_auto_arm_night_when_somebody_home_and_disarmed(make_alarm_with_maps):
    """If the system is disarmed, somebody is at home and it's within the arm-night window, setup() should arm 'night'."""
    calls = []

    # no sensors needed for this test
    app = make_alarm_with_maps({}, {}, {'always': {}})

    # system is currently disarmed
    app.get_alarm_state = lambda: 'disarmed'
    app.is_alarm_disarmed = lambda: True

    # somebody is at home and it's the night arm window
    app.is_somebody_at_home = lambda: True
    app.is_time_in_arm_night_window = lambda: True

    # allow auto-arming
    app.is_auto_arming_allowed = lambda: True

    # capture arming calls
    app.arm_alarm = lambda mode: calls.append(mode)

    app.setup()

    assert 'night' in calls


def test_auto_arm_away_when_disarmed_and_nobody_home(make_alarm_with_maps):
    """If the system is disarmed and nobody is at home, setup() should arm 'away'."""
    calls = []

    app = make_alarm_with_maps({}, {}, {'always': {}})

    # system is disarmed
    app.get_alarm_state = lambda: 'disarmed'
    app.is_alarm_disarmed = lambda: True

    # nobody is at home
    app.is_nobody_at_home = lambda: True

    # allow auto-arming
    app.is_auto_arming_allowed = lambda: True

    app.arm_alarm = lambda mode: calls.append(mode)

    app.setup()

    assert 'away' in calls


def test_do_not_auto_arm_when_guest_mode_enabled_and_nobody_home(make_alarm_with_maps):
    """If guest mode is enabled, the system should not auto-arm even when nobody is home."""
    calls = []

    app = make_alarm_with_maps({}, {}, {'always': {}})

    # system is disarmed
    app.get_alarm_state = lambda: 'disarmed'
    app.is_alarm_disarmed = lambda: True

    # nobody of the normal users is at home
    app.is_nobody_at_home = lambda: True

    # guest mode is enabled which should block auto-arming
    app.in_guest_mode = lambda: True

    # capture any arming calls
    app.arm_alarm = lambda mode: calls.append(mode)

    app.setup()

    # Should not have armed (no calls made)
    assert calls == []


def test_auto_arm_vacation_when_vacation_mode_enabled_and_nobody_home(make_alarm_with_maps):
    """If vacation mode is enabled and nobody is home, setup() should arm 'vacation'."""
    calls = []

    app = make_alarm_with_maps({}, {}, {'always': {}})

    # system is disarmed
    app.get_alarm_state = lambda: 'disarmed'
    app.is_alarm_disarmed = lambda: True

    # nobody is at home
    app.is_nobody_at_home = lambda: True

    # vacation mode is enabled
    app.in_vacation_mode = lambda: True

    # allow auto-arming
    app.is_auto_arming_allowed = lambda: True

    app.arm_alarm = lambda mode: calls.append(mode)

    app.setup()

    assert 'vacation' in calls


def test_disarm_on_device_tracker_return_home(make_alarm_with_maps):
    """When a tracked device returns home and the alarm is armed, presence_change_callback should disarm."""
    calls = []

    app = make_alarm_with_maps({}, {}, {'always': {}})

    # set a device tracker and mark it as tracked
    tracker = 'device_tracker.alice'
    app._device_trackers = [tracker]

    # alarm reports armed
    app.is_alarm_armed = lambda: True
    app.is_alarm_pending = lambda: False
    app.is_alarm_triggered = lambda: False

    # capture disarm calls
    app.disarm_alarm = lambda: calls.append('disarm')

    # simulate presence callback where the tracker comes home
    app.presence_change_callback(tracker, None, 'not_home', 'home', {})

    assert 'disarm' in calls
