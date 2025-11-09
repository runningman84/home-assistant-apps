

def test_fire_alert_triggers_analyze_and_trigger(make_alarm_with_maps):
    calls = []

    device_class_map = {'sensor_fire1': 'temperature'}
    state_map = {'sensor_fire1': '80'}
    sensors = {'always': {'fire': ['sensor_fire1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # capture alarm trigger
    app.call_alarm_control_panel = lambda action: calls.append(action)

    # run analyze_and_trigger which should detect fire and call alarm_trigger
    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls


def test_water_alert_triggers_analyze_and_trigger(make_alarm_with_maps):
    calls = []

    device_class_map = {'sensor_water1': 'moisture'}
    state_map = {'sensor_water1': 'on'}
    sensors = {'always': {'water': ['sensor_water1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.call_alarm_control_panel = lambda action: calls.append(action)

    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls


def test_burglar_alert_triggers_when_armed_away(make_alarm_with_maps):
    calls = []

    device_class_map = {'door1': 'door', 'door2': 'door'}
    state_map = {'door1': 'on', 'door2': 'on'}
    sensors = {'armed_away': {'group1': ['door1', 'door2']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # ensure burglar branch sees the system as armed away
    app.is_alarm_armed_away = lambda: True
    app.is_alarm_armed_vacation = lambda: False

    app.call_alarm_control_panel = lambda action: calls.append(action)

    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls


def test_button_trigger_alarm_calls_alarm_trigger(make_alarm_with_maps):
    calls = []

    app = make_alarm_with_maps({}, {}, {'always': {}})
    app.call_alarm_control_panel = lambda action: calls.append(action)

    # ensure bridge is present and online (handled by helper)
    # provide friendly name for the entity parameter
    app.get_state = lambda entity, attribute=None: 'Button 1' if attribute == 'friendly_name' else 'on'

    app.button_trigger_alarm('some_button_entity')

    assert 'alarm_trigger' in calls


def test_smoke_sensor_triggers_fire_alert(make_alarm_with_maps):
    """Smoke sensors (device_class 'smoke') should trigger a fire alarm."""
    calls = []

    device_class_map = {'sensor_smoke1': 'smoke'}
    state_map = {'sensor_smoke1': 'on'}
    sensors = {'always': {'fire': ['sensor_smoke1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.call_alarm_control_panel = lambda action: calls.append(action)

    app.analyze_and_trigger()

    assert 'alarm_trigger' in calls
