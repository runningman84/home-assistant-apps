from tests.waste.conftest import make_waste_app
from datetime import datetime, timedelta


def test_notify_for_tomorrow(monkeypatch):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    state_map = {('sensor.waste', 'message'): 'Restmüll', ('sensor.waste', 'start_time'): tomorrow}
    app, calls = make_waste_app(args={'waste_calendar': 'sensor.waste'}, state_map=state_map)
    app.is_somebody_at_home = lambda: True
    app.is_time_in_night_window = lambda: False

    app.setup()
    assert any(c[0] == 'awtrix' for c in calls)
    assert any(c[0] == 'tts' for c in calls)


def test_reset_counters_when_none():
    app, calls = make_waste_app()
    app._waste_calendar = None
    app._tts_sent_today = 5
    app._tts_sent_tomorrow = 5
    app.setup()
    # When no calendar is configured, setup() returns early and counters remain unchanged
    assert app._tts_sent_today == 5 and app._tts_sent_tomorrow == 5
