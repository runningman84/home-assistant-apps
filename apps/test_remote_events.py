from tests.light_switch.conftest import make_light_switch_app


def evt(event_type):
    return {'new_state': {'attributes': {'event_type': event_type}}}


def test_brightness_and_toggle():
    app, calls = make_light_switch_app(args={'lights': ['l1'], 'lights_left': ['l2'], 'lights_right': ['l3']})

    app.remote_callback('evt', evt('brightness_up_click'), {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.remote_callback('evt', evt('arrow_left_click'), {})
    assert ('toggle', 'l2') in calls

    calls.clear()
    app.remote_callback('evt', {'new_state': {'attributes': {}}}, {})
    # no event_type -> nothing appended
    assert calls == []


def test_brightness_down_and_right_hold_and_unknown():
    app, calls = make_light_switch_app(args={'lights': ['l1'], 'lights_left': [], 'lights_right': ['l3']}, state_map={'l1': 'on'})

    calls.clear()
    app.remote_callback('evt', evt('brightness_down_click'), {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.get_state = lambda e, attribute=None: 5000 if attribute == 'max_color_temp_kelvin' else 'on'
    app.remote_callback('evt', evt('arrow_right_hold'), {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.remote_callback('evt', evt('not_a_real_event'), {})
    assert calls == []


def test_brightness_holds_and_arrow_right_click():
    app, calls = make_light_switch_app(args={'lights': ['l1'], 'lights_left': [], 'lights_right': ['l3']}, state_map={'l1': 'on'})
    calls.clear()
    app.remote_callback('evt', evt('brightness_up_hold'), {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.remote_callback('evt', evt('brightness_down_hold'), {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.remote_callback('evt', evt('arrow_right_click'), {})
    assert ('toggle', 'l3') in calls


def test_arrow_holds_and_toggle_all():
    app, calls = make_light_switch_app(args={'lights': ['l1', 'l2'], 'lights_left': [], 'lights_right': []}, state_map={'l1': 'on', 'l2': 'off'})
    # arrow_left_hold -> sets color temp to min_color_temp_kelvin for each light
    app.get_state = lambda e, attribute=None: 2000 if attribute == 'min_color_temp_kelvin' else 'on'
    app.remote_callback('evt', {'new_state': {'attributes': {'event_type': 'arrow_left_hold'}}}, {})
    assert any(c[0] == 'turn_on' for c in calls)

    calls.clear()
    app.remote_callback('evt', {'new_state': {'attributes': {'event_type': 'toggle'}}}, {})
    assert any(c[0] == 'toggle' for c in calls)
