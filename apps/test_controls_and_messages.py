from datetime import datetime


def test_ignore_sensors_populates_ignored_and_skips(make_alarm_with_maps):
    device_class_map = {'door1': 'door'}
    state_map = {'door1': 'on'}
    sensors = {'armed_away': {'g': ['door1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # Ensure alerts exist
    alerts = app.get_alerts()
    assert 'burglar' in alerts

    app.ignore_sensors('armed_away')
    assert 'door1' in app._sensors_ignored

    # After ignoring, get_alerts should not return door1
    alerts2 = app.get_alerts()
    assert all('door1' not in lst for lst in alerts2.values())


def test_control_change_callback_triggered_and_disarmed_branches(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})

    called = {'flash': 0, 'media': 0, 'burglar': 0, 'notify': []}

    app.start_flash_warning = lambda *a, **k: called.update({'flash': called['flash'] + 1})
    app.start_media_warning = lambda *a, **k: called.update({'media': called['media'] + 1})
    app.start_burglar_siren = lambda *a, **k: called.update({'burglar': called['burglar'] + 1})
    app.reset_alarm_message = lambda *a, **k: None
    app.stop_fire_siren = lambda *a, **k: None
    app.stop_burglar_siren = lambda *a, **k: None
    app.stop_media_warning = lambda *a, **k: None
    app.stop_flash_warning = lambda *a, **k: None

    # capture notify calls (message, prio)
    app.notify = lambda message, title=None, prio=None: called['notify'].append((message, prio))

    # Triggered branch
    app.get_alarm_state = lambda: 'triggered'
    app.is_alarm_triggered = lambda: True
    app.get_alarm_type = lambda: 'burglar'
    app.get_alarm_message = lambda: 'intruder'

    app.control_change_callback('alarm', None, 'old', 'new', {})

    assert called['flash'] >= 1
    assert called['media'] >= 1
    assert called['burglar'] >= 1
    # notify called with prio == 0 for triggered
    assert any(prio == 0 for (_m, prio) in called['notify'])

    # Disarmed branch should set last disarm and clear sensors
    app._sensors_ignored = ['x']
    app.is_alarm_triggered = lambda: False
    app.is_alarm_pending = lambda: False
    app.is_alarm_arming = lambda: False
    app.is_alarm_disarmed = lambda: True
    app.get_alarm_state = lambda: 'disarmed'

    app.set_alarm_light_color = lambda color, brightness: called.update({'color': (color, brightness)})

    app.control_change_callback('alarm', None, 'old', 'new', {})

    assert isinstance(app._last_disarm_timestamp, datetime)
    assert app._sensors_ignored == []
    assert called.get('color') == ('green', 10)


def test_flash_warning_with_lights_sets_and_cancels_timer(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    app._alarm_lights = ['light.kitchen']

    app.run_in = lambda func, delay, **kw: 'timer-handle'
    canceled = {}
    app.cancel_timer = lambda h: canceled.update({'handle': h})
    app.toggle = lambda light: None

    app.start_flash_warning('red', 50)
    assert app._flash_warning_handle == 'timer-handle'

    app.stop_flash_warning()
    assert canceled.get('handle') == 'timer-handle'
    assert app._flash_warning_handle is None
    assert app._flash_count == 60


def test_media_warning_start_and_stop(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    app.run_in = lambda func, delay, **kw: 'media-handle'
    canceled = {}
    app.cancel_timer = lambda h: canceled.update({'handle': h})
    app.notify_media = lambda message=None, title=None, prio=None: None

    app.start_media_warning()
    assert app._media_warning_handle == 'media-handle'

    app.stop_media_warning()
    assert canceled.get('handle') == 'media-handle'
    assert app._media_warning_handle is None
    assert app._media_warning_count == app._media_warning_max_count


def test_alarm_button_event_permutations(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    calls = []

    app.is_alarm_disarmed = lambda: True
    app.button_arm_home = lambda e: calls.append(('home', e))
    app.button_arm_away = lambda e: calls.append(('away', e))
    app.button_disarm = lambda e: calls.append(('disarm', e))
    app.button_trigger_alarm = lambda e: calls.append(('trigger', e))

    # helper to craft event data
    def event_for(t):
        return {'entity_id': 'button.1', 'new_state': {'attributes': {'event_type': t}}}

    app.alarm_button_callback('evt', event_for('single'), {})
    app.alarm_button_callback('evt', event_for('double'), {})
    app.alarm_button_callback('evt', event_for('hold'), {})
    app.alarm_button_callback('evt', event_for('triple'), {})

    assert ('home', 'button.1') in calls
    assert ('away', 'button.1') in calls
    assert ('disarm', 'button.1') in calls
    assert ('trigger', 'button.1') in calls


def test_button_trigger_alarm_negative_branches(make_alarm_with_maps):
    calls = []
    app = make_alarm_with_maps({}, {}, {'always': {}})
    app.call_alarm_control_panel = lambda action: calls.append(action)

    # bridge off
    app.get_state = lambda e, attribute=None: 'off' if e == 'binary_sensor.zigbee2mqtt_bridge_connection_state' else None
    app.button_trigger_alarm('ent')
    assert calls == []

    # bridge on but recently updated (<300s)
    calls.clear()
    app.get_state = lambda e, attribute=None: 'on' if e == 'binary_sensor.zigbee2mqtt_bridge_connection_state' else None
    app.get_seconds_since_update = lambda e: 100
    app.button_trigger_alarm('ent')
    assert calls == []


def test_trigger_alarm_sets_type_message_and_calls_panel(make_alarm_with_maps):
    calls = []
    app = make_alarm_with_maps({}, {}, {'always': {}})

    app.create_alarm_message = lambda alerts: 'ALERT_MSG'
    app.notify_awtrix = lambda message, *a, **k: calls.append(('awtrix', message))
    app.call_alarm_control_panel = lambda action: calls.append(('svc', action))

    app.trigger_alarm('fire', {'fire': ['s1']})

    assert app.get_alarm_type() == 'fire'
    assert app.get_alarm_message() == 'ALERT_MSG'
    assert ('svc', 'alarm_trigger') in calls


def test_optimize_and_create_message_formats_and_pluralization(make_alarm_with_maps):
    device_class_map = {'m1': 'motion', 'm2': 'motion'}
    state_map = {'m1': 'on', 'm2': 'on'}
    sensors = {'always': {'burglar': ['m1', 'm2']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # add friendly names
    def fake_get_state(entity, attribute=None):
        if attribute == 'friendly_name':
            return 'Kitchen Bewegungsmelder'
        if attribute == 'device_class':
            return device_class_map.get(entity)
        return state_map.get(entity)

    app.get_state = fake_get_state
    app._alarm_type = 'burglar'
    app._language = 'english'
    app._translation['english']['burglar_alert'] = 'Burglar!'
    app._translation['english']['sensor_info_motion_single'] = '{} motion happened'
    app._translation['english']['sensor_info_motion_multi'] = '{} motions happened'

    # build alerts map and get message
    alerts = {'burglar': ['m1', 'm2']}
    msg = app.create_alarm_message(alerts)
    assert 'Burglar' in msg or 'Burglar!' in msg
    assert 'motion' in msg


def test_classify_sensor_and_alarm_return_expected(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    # mapping present in fixture
    assert app.classify_sensor('motion') == 'motion' or app.classify_sensor('motion') is not None
    assert app.classify_alarm('motion') in ('burglar', 'fire', 'water') or app.classify_alarm('motion') is not None
    assert app.classify_sensor('unknown_class') is None
    assert app.classify_alarm('unknown_class') is None


def test_periodic_time_callback_invokes_setup_and_analyze(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    called = {'setup': 0, 'analyze': 0}
    app.setup = lambda: called.update({'setup': called['setup'] + 1})
    app.analyze_and_trigger = lambda: called.update({'analyze': called['analyze'] + 1})

    app.periodic_time_callback({})
    assert called['setup'] == 1
    assert called['analyze'] == 1


def test_presence_change_callback_non_tracker_calls_setup(make_alarm_with_maps):
    app = make_alarm_with_maps({}, {}, {'always': {}})
    called = {'setup': 0}
    app.setup = lambda: called.update({'setup': called['setup'] + 1})

    app._device_trackers = ['device_tracker.x']
    # call presence_change_callback with a non-tracker entity
    app.presence_change_callback('sensor.other', None, 'old', 'new', {})
    assert called['setup'] == 1


def test_call_alarm_control_panel_calls_service_with_pin(make_alarm_with_maps):
    calls = []
    app = make_alarm_with_maps({}, {}, {'always': {}})
    app._alarm_pin = '1234'
    app._alarm_control_panel = 'alarm_control_panel.ha'
    app.call_service = lambda svc, **kw: calls.append((svc, kw))

    app.call_alarm_control_panel('alarm_arm_home')
    assert calls[0][0] == 'alarm_control_panel/alarm_arm_home'
    assert calls[0][1].get('code') == '1234'


def test_is_sensor_monitored_various_cases(make_alarm_with_maps):
    # sensor present in armed_away desired state
    sensors = {'armed_away': {'g': ['s1']}, 'always': {}}
    app = make_alarm_with_maps({}, {}, sensors)
    app.get_alarm_state = lambda: 'armed_away'
    app._arming_state = 'armed_away'
    assert app.is_sensor_monitored('s1') is True

    # in ignore list
    app._sensors_ignored = ['s1']
    assert app.is_sensor_monitored('s1') is False


def test_count_alerts_by_arming_state_counts_correctly(make_alarm_with_maps):
    device_class_map = {'d1': 'door', 'm1': 'motion'}
    state_map = {'d1': 'on', 'm1': 'on'}
    sensors = {'armed_away': {'g': ['d1', 'm1']}, 'always': {}}
    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    count = app.count_alerts_by_arming_state('armed_away')
    assert count >= 2
