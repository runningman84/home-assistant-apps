from datetime import datetime, timezone, timedelta

from tests.base.factories import make_base_app


def test_internal_change_timing_marks_change_internal_and_expires():
    app = make_base_app()

    # Initially, no internal record -> current change is external
    assert app.is_current_change_external() is True

    # Record an internal change (should make current change internal)
    app.record_internal_change()
    assert app.is_current_change_external() is False

    # Simulate internal change being older than the internal timeout
    now = datetime.now(timezone.utc)
    app._internal_change_timestamp = now - timedelta(seconds=app.get_internal_change_timeout() + 5)

    # Now the internal timeout window expired -> change should be considered external
    assert app.is_current_change_external() is True


def test_external_change_blocks_internal_actions_until_timeout_when_somebody_home():
    app = make_base_app()

    # Make the home presence report someone at home so the 'nobody at home' shortcut does not apply
    original_get_state = app.get_state

    def get_state_home(entity, attribute=None):
        if entity == "device_tracker.phone1":
            return "home"
        return original_get_state(entity, attribute=attribute)

    app.get_state = get_state_home

    # Record an external change now
    app.record_external_change()
    assert app.is_last_change_external() is True

    # Immediately after an external change, internal changes should NOT be allowed
    assert app.is_internal_change_allowed() is False

    # Fast-forward external change beyond the configured external timeout
    now = datetime.now(timezone.utc)
    app._external_change_timestamp = now - timedelta(seconds=app.get_external_change_timeout() + 2)

    # Now internal changes should be allowed again
    assert app.is_internal_change_allowed() is True


def test_get_remaining_seconds_before_internal_change_reports_expected_range():
    app = make_base_app()

    # Set an external change 60 seconds ago
    now = datetime.now(timezone.utc)
    app._external_change_timestamp = now - timedelta(seconds=60)

    rem = app.get_remaining_seconds_before_internal_change_is_allowed()
    # remaining should be slightly less than timeout but positive
    assert rem <= app.get_external_change_timeout()
    assert rem >= app.get_external_change_timeout() - 61


def test_invalid_external_timeout_returns_zero_remaining():
    app = make_base_app()

    # set invalid timeout and a recent external change
    app._external_change_timeout = -1
    app.record_external_change()

    rem = app.get_remaining_seconds_before_internal_change_is_allowed()
    assert rem == 0
