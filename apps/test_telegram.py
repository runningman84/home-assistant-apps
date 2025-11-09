from tests.telegram.conftest import make_telegram_app


def test_alarm_state_changed_sends_messages():
    app, calls = make_telegram_app(args={'user_ids': [111]}, state_map={})
    app._alarm_control_panel = 'alarm.panel'
    app.get_state = lambda e, attribute=None: 'disarmed' if e == 'alarm.panel' else None
    app._user_ids = [111]
    app.alarm_state_changed_callback('alarm.panel', None, 'armed', 'disarmed', {})
    assert any(c[0] == 'telegram_bot/send_message' for c in calls)


def test_receive_callback_arm_home_edits_message():
    app, calls = make_telegram_app()
    payload = {'data': '/alarm_arm_home', 'id': 'cb1', 'user_id': 111, 'message': {'message_id': 10, 'chat': {'id': 222}}}
    app._alarm_control_panel = 'alarm.panel'
    app._alarm_pin = '1234'
    app.get_state = lambda e, attribute=None: 'disarmed'
    app.receive_telegram_callback_alarm('telegram_callback', payload)
    assert any('alarm_control_panel/alarm_arm_home' in c[0] or c[0] == 'telegram_bot/answer_callback_query' or c[0] == 'telegram_bot/edit_message' for c in calls)

def test_alarm_state_changed_keyboard_variants():
    app, calls = make_telegram_app()
    app._alarm_control_panel = 'alarm.panel'
    app._user_ids = [1, 2]

    # disarmed state -> should send keyboard with arm options
    app.get_state = lambda e, attribute=None: 'disarmed'
    calls.clear()
    app.alarm_state_changed_callback('ent', 'attr', 'armed', 'disarmed', {})
    assert any(c[0] == 'telegram_bot/send_message' for c in calls)

    # triggered state -> should send immediate notification (disable_notification False)
    app.get_state = lambda e, attribute=None: 'triggered'
    calls.clear()
    app.alarm_state_changed_callback('ent', 'attr', 'armed', 'triggered', {})
    assert any(c[0] == 'telegram_bot/send_message' for c in calls)


def test_receive_command_alarm_status_variants():
    app, calls = make_telegram_app()
    app._alarm_control_panel = 'alarm.panel'

    # disarmed status - send_message should be called
    app.get_state = lambda e, attribute=None: 'disarmed'
    payload = {'user_id': 111}
    calls.clear()
    app.receive_telegram_command_alarm_status('telegram_command', payload)
    assert any(c[0] == 'telegram_bot/send_message' for c in calls)
