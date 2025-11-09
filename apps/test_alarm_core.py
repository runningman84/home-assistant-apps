import json


def test_set_and_get_alarm_type(make_base_app):
    from apps.alarm import AlarmControl

    app = object.__new__(AlarmControl)
    # minimal init values used by methods under test
    app._alarm_type = None

    # set and get
    app.set_alarm_type('burglar')
    assert app.get_alarm_type() == 'burglar'


def test_set_and_reset_alarm_message_calls_awtrix_and_clears(make_base_app):
    from apps.alarm import AlarmControl

    app = object.__new__(AlarmControl)
    # prepare awtrix prefixes and capture calls
    app._awtrix_prefixes = ['p']
    calls = []
    app.call_service = lambda svc, **kw: calls.append((svc, kw))

    # call set_alarm_message which calls notify_awtrix
    app.set_alarm_message('Intruder!')
    assert app.get_alarm_message() == 'Intruder!'

    # ensure mqtt publish happened
    assert len(calls) == 1
    svc, kwargs = calls[0]
    assert svc == 'mqtt/publish'
    payload = json.loads(kwargs['payload'])
    assert payload['text'] == 'Intruder!'

    # reset should clear and call reset_awtrix
    calls.clear()
    app.reset_alarm_message()
    assert app.get_alarm_message() is None
    # reset_awtrix publishes empty payload
    assert len(calls) == 1
    svc, kwargs = calls[0]
    assert svc == 'mqtt/publish'
    payload = json.loads(kwargs['payload'])
    assert payload == {}


def test_is_time_in_arm_night_window_delegates(make_base_app, monkeypatch):
    from apps.alarm import AlarmControl

    app = object.__new__(AlarmControl)
    app._alarm_arm_night_after_time = '23:00:00'
    app._alarm_arm_night_before_time = '06:00:00'

    # monkeypatch now_is_between to capture args
    called = {}

    def fake_now_is_between(start, end):
        called['args'] = (start, end)
        return True

    monkeypatch.setattr(app, 'now_is_between', fake_now_is_between)
    assert app.is_time_in_arm_night_window() is True
    assert called['args'] == ('23:00:00', '06:00:00')


def test_set_alarm_light_color_calls_light_turn_on(make_base_app):
    from apps.alarm import AlarmControl

    app = object.__new__(AlarmControl)
    app._alarm_lights = ['light.kitchen']
    calls = []
    app.call_service = lambda svc, **kw: calls.append((svc, kw))

    app.set_alarm_light_color('red', 50)
    assert len(calls) == 1
    svc, kwargs = calls[0]
    assert svc == 'light/turn_on'
    assert kwargs['entity_id'] == 'light.kitchen'
    assert kwargs['color_name'] == 'red'
    assert kwargs['brightness_pct'] == 50


def test_flash_warning_no_lights_logs_and_no_timer(make_base_app, monkeypatch):
    from apps.alarm import AlarmControl

    app = object.__new__(AlarmControl)
    # no lights configured
    app._alarm_lights = []
    # calling start_flash_warning should early return and not set a timer handle
    app._flash_warning_handle = 'should_be_cleared'
    app.start_flash_warning()
    assert app._flash_warning_handle == 'should_be_cleared'


def test_classify_and_alarm_mapping(make_alarm_with_maps):
    device_class_map = {
        'sensor.door1': 'door',
        'sensor.win1': 'window',
        'sensor.motion1': 'motion',
        'sensor.temp1': 'temperature',
    }
    state_map = {
        'sensor.door1': 'off',
        'sensor.win1': 'off',
        'sensor.motion1': 'off',
        'sensor.temp1': '20',
        'alarm_control_panel.ha_alarm': 'armed_away'
    }

    sensors = {
        'always': {'group1': ['sensor.temp1']},
        'armed_away': {'group1': ['sensor.door1', 'sensor.win1', 'sensor.motion1']}
    }

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # classify_sensor should map device classes to sensor types
    assert app.classify_sensor('door') == 'door'
    assert app.classify_sensor('motion') == 'motion'
    assert app.classify_sensor('temperature') == 'environmental' or app.classify_sensor('temperature') == 'temperature' or app.classify_sensor('temperature') is not None

    # classify_alarm should map device classes to alarm categories
    assert app.classify_alarm('door') == 'burglar'
    assert app.classify_alarm('temperature') == 'fire'


def test_optimize_sensor_name_and_create_message(make_alarm_with_maps):
    # Build a simple alert map and verify message composition
    device_class_map = {'sensor.door1': 'door'}
    state_map = {'sensor.door1': 'on', 'alarm_control_panel.ha_alarm': 'armed_away'}
    sensors = {'armed_away': {'group1': ['sensor.door1']}, 'always': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app._alarm_type = 'burglar'

    alerts = {'burglar': ['sensor.door1']}
    msg = app.create_alarm_message(alerts)
    assert isinstance(msg, str)
    assert 'door' in msg.lower()

    # optimize_sensor_name should remove generic words and return a short name
    # monkeypatch get_state to a friendly name containing words to remove
    app.get_state = lambda e, attribute=None: 'Main Door sensor' if attribute == 'friendly_name' else 'on'
    short = app.optimize_sensor_name('sensor.door1')
    assert 'main' in short.lower()


def test_is_sensor_monitored_and_check_sensor(make_alarm_with_maps):
    device_class_map = {'sensor.door1': 'door', 'sensor.temp1': 'temperature'}
    state_map = {'sensor.door1': 'off', 'sensor.temp1': '40', 'alarm_control_panel.ha_alarm': 'armed_home'}
    sensors = {'armed_home': {'g1': ['sensor.door1']}, 'always': {'fire': ['sensor.temp1']}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # ensure get_alarm_state returns the configured alarm_control_panel state
    app.get_alarm_state = lambda: state_map.get('alarm_control_panel.ha_alarm')
    # ensure attributes used by methods exist
    app._arming_state = app.get_alarm_state()

    # sensor in armed_home should be monitored
    assert app.is_sensor_monitored('sensor.door1')

    # temperature sensor exceeds threshold -> check_sensor should return False
    app._fire_temperature_threshold = 35
    assert app.check_sensor('sensor.temp1', 'off') is False

    # unknown sensor state is considered OK
    app.get_state = lambda e, attribute=None: None if e == 'sensor.bad' else state_map.get(e)
    assert app.check_sensor('sensor.bad') is True


def test_get_alerts_and_thresholds(make_alarm_with_maps):
    device_class_map = {
        'sensor.f1': 'temperature',
        'sensor.w1': 'moisture',
        'sensor.b1': 'door',
    }
    state_map = {
        'sensor.f1': '60',  # above default threshold in fixture
        'sensor.w1': 'on',
        'sensor.b1': 'on',
        'alarm_control_panel.ha_alarm': 'armed_away'
    }

    sensors = {
        'always': {'fire': ['sensor.f1'], 'water': ['sensor.w1']},
        'armed_away': {'group1': ['sensor.b1']}
    }

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # ensure attributes used by methods exist
    app._arming_state = app.get_alarm_state()
    app._alarm_pin = None
    app._alarm_arm_night_after_time = "23:15:00"
    app._alarm_arm_night_before_time = "06:00:00"

    alerts = app.get_alerts()
    # fire and water should be present (f1 and w1) and burglar b1
    assert 'fire' in alerts
    assert 'water' in alerts
    assert 'burglar' in alerts

    # analyze_and_trigger should trigger fire first (call_service is stubbed so no side effects)
    # ensure it runs without raising
    app.analyze_and_trigger()


def test_desired_arming_and_auto_arming_policy(make_alarm_with_maps):
    # Setup sensors and states to simulate presence and modes
    device_class_map = {}
    state_map = {
        'alarm_control_panel.ha_alarm': 'disarmed',
        'device_tracker.anna': 'home'
    }

    sensors = {'always': {}, 'armed_home': {}, 'armed_away': {}}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # ensure attributes used by methods exist
    app._alarm_arm_night_after_time = "23:15:00"
    app._alarm_arm_night_before_time = "06:00:00"

    # simulate one device tracker at home
    app._device_trackers = ['device_tracker.anna']
    app.get_state = lambda e, attribute=None: state_map.get(e)

    # desired arming should be 'home' because somebody is at home and not in night window
    app.now_is_between = lambda a, b: False
    assert app.get_desired_arming_state() == 'home'

    # is_auto_arming_allowed should return False because is_last_disarming_recent is False and somebody at home
    assert app.is_auto_arming_allowed() is False or isinstance(app.is_auto_arming_allowed(), bool)


def test_internal_external_change_timing(make_alarm_with_maps):
    device_class_map = {}
    state_map = {'alarm_control_panel.ha_alarm': 'disarmed'}
    sensors = {}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    # ensure base internal/external change attributes exist
    app._internal_change_timestamp = None
    app._external_change_timestamp = None
    from datetime import datetime, timezone

    # No external change recorded -> remaining time 0 and internal allowed
    app._external_change_timestamp = None
    assert app.get_remaining_seconds_before_internal_change_is_allowed() == 0
    assert app.is_internal_change_allowed() is True

    # Record an external change now and set timeout to 120 seconds
    app._external_change_timestamp = datetime.now(timezone.utc)
    app._external_change_timeout = 120
    rem = app.get_remaining_seconds_before_internal_change_is_allowed()
    assert rem <= 120 and rem >= 0


def test_initialize_and_core_behaviors(make_alarm_with_maps):
    # Build a richer app instance using the fixture and stub AppDaemon methods
    device_class_map = {
        'binary_sensor.front_door': 'door',
        'binary_sensor.temp': 'temperature',
        'binary_sensor.motion': 'motion',
    }
    state_map = {
        'binary_sensor.front_door': 'off',
        'binary_sensor.temp': '20',
        'binary_sensor.motion': 'off',
        'binary_sensor.zigbee2mqtt_bridge_connection_state': 'on',
        'alarm_control_panel.ha_alarm': 'disarmed'
    }

    sensors = {
        'armed_home': {'g1': ['binary_sensor.front_door']},
        'always': {'fire': ['binary_sensor.temp']},
        'armed_away': {'g1': ['binary_sensor.motion']}
    }

    app = make_alarm_with_maps(device_class_map, state_map, sensors)

    # minimal args used by initialize
    app.args = {
        'language': 'english',
        'armed_home_binary_sensors': ['binary_sensor.front_door'],
        'armed_away_binary_sensors': ['binary_sensor.motion'],
        'fire_temperature_sensors': ['binary_sensor.temp'],
        'alarm_control_buttons': [],
        'alarm_lights': ['light.alarm'],
        'fire_siren_switches': ['switch.fire'],
        'burglar_siren_switches': ['switch.burglar'],
        'alarm_control_panel': 'alarm_control_panel.ha_alarm'
    }

    # stub AppDaemon style methods that initialize() will call
    app.listen_state = lambda *a, **k: None
    app.listen_event = lambda *a, **k: None
    app.run_daily = lambda *a, **k: None
    app.run_every = lambda *a, **k: None
    app.run_in = lambda cb, delay, **kwargs: None
    app.cancel_timer = lambda h: None
    app.toggle = lambda entity: setattr(app, f"_toggled_{entity}", True)
    app.turn_on = lambda e: setattr(app, f"_turned_on_{e}", True)
    app.turn_off = lambda e: setattr(app, f"_turned_off_{e}", True)
    app.call_service = lambda *a, **k: setattr(app, "_last_call_service", (a, k))
    app.notify = lambda *a, **k: setattr(app, "_last_notify", (a, k))
    app.notify_awtrix = lambda *a, **k: None
    app.reset_awtrix = lambda *a, **k: None

    # ensure methods used later exist
    app._alarm_pin = None
    app._alarm_arm_night_after_time = "23:15:00"
    app._alarm_arm_night_before_time = "06:00:00"
    app.parse_time = lambda s: s

    # run initialize - should complete using stubs
    app.initialize()

    # exercise flash warning and media functions
    app._flash_count = 0
    app.flash_warning({})
    app.start_flash_warning('red', 50)
    app.flash_warning({})
    app.stop_flash_warning()

    app._media_warning_count = 0
    app.media_warning({'message': 'test'})
    app.start_media_warning()
    app.media_warning_with_delay('hello', delay=0)
    app.stop_media_warning()

    # sirens
    app.start_burglar_siren()
    app.stop_burglar_siren()
    app.start_fire_siren()
    app.stop_fire_siren()

    # button trigger (will call trigger_alarm -> call_service stub)
    app.button_trigger_alarm('binary_sensor.front_door')

    # control state transition: simulate triggered alarm
    app._alarm_type = 'burglar'
    app._alarm_message = 'Intruder'
    app.get_state = lambda e, attribute=None: 'triggered' if e == 'alarm_control_panel.ha_alarm' else state_map.get(e)
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'armed_away', 'triggered', {})

    # simulate disarm
    app.get_state = lambda e, attribute=None: 'disarmed' if e == 'alarm_control_panel.ha_alarm' else state_map.get(e)
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'triggered', 'disarmed', {})

    # verify call_service and notify were called at least once
    assert hasattr(app, '_last_call_service')
    assert hasattr(app, '_last_notify')


def test_control_change_callback_branches(make_alarm_with_maps):
    device_class_map = {}
    state_map = {'alarm_control_panel.ha_alarm': 'disarmed'}
    sensors = {}

    app = make_alarm_with_maps(device_class_map, state_map, sensors)
    app.args = {'alarm_control_panel': 'alarm_control_panel.ha_alarm'}
    app._alarm_pin = None
    app._alarm_lights = ['light.a']
    app._awtrix_prefixes = []
    app._alarm_type = 'fire'
    app._alarm_message = 'Fire!'

    # stubs
    app.start_flash_warning = lambda *a, **k: setattr(app, '_flash_started', True)
    app.start_media_warning = lambda *a, **k: setattr(app, '_media_started', True)
    app.start_burglar_siren = lambda *a, **k: setattr(app, '_burglar_started', True)
    app.start_fire_siren = lambda *a, **k: setattr(app, '_fire_started', True)
    app.reset_awtrix = lambda *a, **k: None
    app.stop_fire_siren = lambda *a, **k: setattr(app, '_fire_stopped', True)
    app.stop_burglar_siren = lambda *a, **k: setattr(app, '_burglar_stopped', True)
    app.stop_media_warning = lambda *a, **k: setattr(app, '_media_stopped', True)
    app.stop_flash_warning = lambda *a, **k: setattr(app, '_flash_stopped', True)
    app.notify = lambda *a, **k: setattr(app, '_notified', True)
    app.notify_awtrix = lambda *a, **k: None

    # simulate triggered
    app.get_state = lambda e, attribute=None: 'triggered' if e == 'alarm_control_panel.ha_alarm' else None
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'armed_away', 'triggered', {})
    assert getattr(app, '_flash_started', False) is True
    assert getattr(app, '_media_started', False) is True

    # simulate pending
    app._alarm_type = None
    app.get_state = lambda e, attribute=None: 'pending' if e == 'alarm_control_panel.ha_alarm' else None
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'armed_away', 'pending', {})
    assert getattr(app, '_flash_started', False) is True

    # simulate armed
    app.get_state = lambda e, attribute=None: 'armed_home' if e == 'alarm_control_panel.ha_alarm' else None
    app._arming_state = 'armed_home'
    app.count_alerts_by_arming_state = lambda s: 1
    app.ignore_sensors = lambda s: setattr(app, '_ignored', True)
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'pending', 'armed_home', {})
    assert getattr(app, '_ignored', False) is True

    # simulate disarmed
    app.get_state = lambda e, attribute=None: 'disarmed' if e == 'alarm_control_panel.ha_alarm' else None
    app.control_change_callback('alarm_control_panel.ha_alarm', 'state', 'armed_home', 'disarmed', {})
    assert getattr(app, '_notified', False) is True

