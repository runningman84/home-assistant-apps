from datetime import datetime, timedelta, timezone


def test_get_night_times_non_workday(make_base_app, monkeypatch):
    app = make_base_app()

    # Force is_workday_today/tomorrow to return False
    monkeypatch.setattr(app, "is_workday_today", lambda: False)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: False)

    start, end = app.get_night_times()
    assert start == "23:15:00"
    assert end == "08:30:00"


def test_get_night_times_workday_logic(make_base_app, monkeypatch):
    app = make_base_app()

    # If tomorrow is workday we should pick _night_start_workday for start
    # If today is workday we should pick _night_end_workday for end
    monkeypatch.setattr(app, "is_workday_today", lambda: True)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: True)

    start, end = app.get_night_times()
    assert start == "22:15:00"
    assert end == "06:30:00"


def test_is_time_in_night_window_delegates(make_base_app, monkeypatch):
    app = make_base_app()

    # Replace now_is_between to verify delegation and return value passthrough
    called = {}

    def fake_now_is_between(start, end):
        called['args'] = (start, end)
        return True

    monkeypatch.setattr(app, "get_night_times", lambda: ("aa","bb"))
    monkeypatch.setattr(app, "now_is_between", fake_now_is_between)

    assert app.is_time_in_night_window() is True
    assert called['args'] == ("aa", "bb")


def test_get_seconds_until_night_end_future(make_base_app, monkeypatch):
    app = make_base_app()

    # Set a night_end a minute from now
    now = datetime.now(timezone.utc)
    future_time = (now + timedelta(minutes=1)).time().strftime("%H:%M:%S")

    monkeypatch.setattr(app, "get_night_times", lambda: ("00:00:00", future_time))

    seconds = app.get_seconds_until_night_end()
    assert isinstance(seconds, int)
    # Should be roughly 60 seconds (allow for a few seconds of execution time)
    assert 0 < seconds <= 120


def test_get_seconds_until_night_end_past(make_base_app, monkeypatch):
    app = make_base_app()

    # Set a night_end earlier than now (yesterday) so the function rolls it to next day
    now = datetime.now(timezone.utc)
    past_time = (now - timedelta(hours=1)).time().strftime("%H:%M:%S")
    monkeypatch.setattr(app, "get_night_times", lambda: ("00:00:00", past_time))

    seconds = app.get_seconds_until_night_end()
    # If night end was 1 hour ago, it will be rolled to next day -> ~23 hours
    assert seconds > 3600


def _make_now_is_between_for_fixed_time(fixed_time):
    """Return a now_is_between(start_str, end_str) implementation that
    checks whether fixed_time (a datetime.time) lies in the interval
    start_str..end_str. Handles overnight wrap (start > end).
    """
    from datetime import datetime

    def _now_is_between(start_str, end_str):
        start_t = datetime.strptime(start_str, "%H:%M:%S").time()
        end_t = datetime.strptime(end_str, "%H:%M:%S").time()

        if start_t <= end_t:
            return start_t <= fixed_time < end_t
        # overnight window (e.g., 23:15 -> 08:30)
        return fixed_time >= start_t or fixed_time < end_t

    return _now_is_between


def test_time_1500_is_not_night(make_base_app, monkeypatch):
    app = make_base_app()
    # Ensure we use the non-workday night window (23:15->08:30) so this test
    # is deterministic regardless of the day the test runs on.
    monkeypatch.setattr(app, "is_workday_today", lambda: False)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: False)
    # 15:00 should not be in the default night window (23:15-08:30)
    from datetime import time
    monkeypatch.setattr(app, "now_is_between", _make_now_is_between_for_fixed_time(time(15, 0)))
    assert app.is_time_in_night_window() is False


def test_time_0300_is_night(make_base_app, monkeypatch):
    app = make_base_app()
    # Ensure we use the non-workday night window (23:15->08:30) so this test
    # is deterministic regardless of the day the test runs on.
    monkeypatch.setattr(app, "is_workday_today", lambda: False)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: False)
    # 03:00 should be in the default night window
    from datetime import time
    monkeypatch.setattr(app, "now_is_between", _make_now_is_between_for_fixed_time(time(3, 0)))
    assert app.is_time_in_night_window() is True


def test_time_2330_is_night(make_base_app, monkeypatch):
    app = make_base_app()
    # Ensure we use the non-workday night window (23:15->08:30) so this test
    # is deterministic regardless of the day the test runs on.
    monkeypatch.setattr(app, "is_workday_today", lambda: False)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: False)
    # 23:30 falls after 23:15 -> night
    from datetime import time
    monkeypatch.setattr(app, "now_is_between", _make_now_is_between_for_fixed_time(time(23, 30)))
    assert app.is_time_in_night_window() is True


def test_time_0829_is_night_but_0830_is_not(make_base_app, monkeypatch):
    app = make_base_app()
    # Ensure we use the non-workday night window (23:15->08:30) so this test
    # is deterministic regardless of the day the test runs on.
    monkeypatch.setattr(app, "is_workday_today", lambda: False)
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: False)
    from datetime import time
    monkeypatch.setattr(app, "now_is_between", _make_now_is_between_for_fixed_time(time(8, 29)))
    assert app.is_time_in_night_window() is True

    monkeypatch.setattr(app, "now_is_between", _make_now_is_between_for_fixed_time(time(8, 30)))
    assert app.is_time_in_night_window() is False


def test_night_starts_earlier_if_tomorrow_workday(make_base_app, monkeypatch):
    """If tomorrow is a workday the night start should come from _night_start_workday."""
    app = make_base_app()
    # configure workday-specific starts/ends
    app._night_start = "23:15:00"
    app._night_start_workday = "22:00:00"
    app._night_end = "08:30:00"
    app._night_end_workday = "06:30:00"

    # tomorrow is workday, today is not
    monkeypatch.setattr(app, "is_workday_tomorrow", lambda: True)
    monkeypatch.setattr(app, "is_workday_today", lambda: False)

    start, end = app.get_night_times()
    assert start == "22:00:00"
    assert end == "08:30:00"
