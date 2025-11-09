from tests.weather.conftest import make_weather_app
from datetime import datetime, timedelta, timezone


def make_warning_state(now_offset_hours=2):
    end = (datetime.now(timezone.utc) + timedelta(hours=now_offset_hours)).isoformat()
    return {
        'sensor.current': '1',
        ('sensor.current', 'warning_count'): 1,
        ('sensor.current', 'warning_1_name'): 'Warnung1',
        ('sensor.current', 'warning_1_headline'): 'Starkes Ereignis',
        ('sensor.current', 'warning_1_description'): 'Details',
        ('sensor.current', 'warning_1_start'): datetime.now(timezone.utc).isoformat(),
        ('sensor.current', 'warning_1_end'): end,
    }


def test_process_warnings_sends_awtrix_and_tts():
    state_map = make_warning_state()
    # provide a harmless future sensor state so process_warnings has a value
    state_map['sensor.future'] = '0'
    app, calls = make_weather_app(args={'current_warn_sensor': 'sensor.current', 'future_warn_sensor': 'sensor.future'}, state_map=state_map)
    app._current_warn_sensor = 'sensor.current'
    app.is_somebody_at_home = lambda: True
    app.is_time_in_night_window = lambda: False

    app.handle_warnings()
    assert any(c[0] == 'awtrix' for c in calls)
    assert any(c[0] == 'tts' for c in calls)
