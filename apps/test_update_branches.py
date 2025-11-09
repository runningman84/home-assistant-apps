from tests.power.conftest import make_power_app


def test_update_skips_when_internal_change_not_allowed():
    app, calls = make_power_app()
    # simulate internal change not allowed
    app.is_internal_change_allowed = lambda: False
    app.get_remaining_seconds_before_internal_change_is_allowed = lambda: 5
    app.turn_off_power = lambda: calls.append(('off', 'should_not'))
    app.turn_on_power = lambda: calls.append(('on', 'should_not'))

    app.update_power()
    assert calls == []


def test_update_turns_off_when_nobody_home():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: True
    app.turn_off_power = lambda: calls.append(('off', 'nobody'))

    app.update_power()
    assert ('off', 'nobody') in calls


def test_update_turns_off_when_in_vacation():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: True
    app.turn_off_power = lambda: calls.append(('off', 'vac'))

    app.update_power()
    assert ('off', 'vac') in calls


def test_update_skips_when_media_playing():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_media_players = lambda state, sources=None: 1
    app.turn_off_power = lambda: calls.append(('off', 'media'))

    app.update_power()
    assert calls == []


def test_update_turns_off_on_no_motion_but_sensors_exist():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_media_players = lambda state, sources=None: 0
    app.count_on_motion_sensors = lambda: 0
    app.count_motion_sensors = lambda: 2
    app.get_last_motion = lambda: 123.0
    app.turn_off_power = lambda: calls.append(('off', 'motion'))

    app.update_power()
    assert ('off', 'motion') in calls


def test_update_turns_off_on_alarm_states():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_media_players = lambda state, sources=None: 0
    app.count_on_motion_sensors = lambda: 1
    app.count_motion_sensors = lambda: 1
    app.is_alarm_armed_away = lambda: True
    app.is_alarm_armed_vacation = lambda: False
    app.turn_off_power = lambda: calls.append(('off', 'alarm_away'))

    app.update_power()
    assert ('off', 'alarm_away') in calls


def test_update_noop_when_alarm_triggered_or_pending():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_media_players = lambda state, sources=None: 0
    app.count_on_motion_sensors = lambda: 1
    app.count_motion_sensors = lambda: 1
    app.is_alarm_armed_away = lambda: False
    app.is_alarm_armed_vacation = lambda: False
    app.is_alarm_triggered = lambda: True
    app.is_alarm_pending = lambda: False
    app.turn_on_power = lambda: calls.append(('on', 'should_not'))
    app.turn_off_power = lambda: calls.append(('off', 'should_not'))

    app.update_power()
    assert calls == []


def test_update_turns_on_when_all_conditions_clear():
    app, calls = make_power_app()
    app.is_internal_change_allowed = lambda: True
    app.is_nobody_at_home = lambda: False
    app.in_vacation_mode = lambda: False
    app.count_media_players = lambda state, sources=None: 0
    app.count_on_motion_sensors = lambda: 1
    app.count_motion_sensors = lambda: 1
    app.is_alarm_armed_away = lambda: False
    app.is_alarm_armed_vacation = lambda: False
    app.is_alarm_triggered = lambda: False
    app.is_alarm_pending = lambda: False

    # stub last motion and turn_on_power to record its invocation
    app.get_last_motion = lambda: 0.0
    app.turn_on_power = lambda: calls.append(('on', 'clear'))

    app.update_power()
    assert ('on', 'clear') in calls
