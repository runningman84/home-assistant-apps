from tests.waste.conftest import make_waste_app
from datetime import datetime


def test_seconds_until_tomorrow_and_today_notification():
    app, calls = make_waste_app()
    secs = app.seconds_until_tomorrow()
    assert isinstance(secs, int)

    # simulate collection today
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    app.get_state = lambda e, attribute=None: 'Heute' if attribute == 'message' else today
    app._waste_calendar = 'sensor.waste'
    app.is_somebody_at_home = lambda: True
    app.is_time_in_night_window = lambda: False
    calls.clear()
    app.setup()
    assert any(c[0] == 'awtrix' for c in calls)
