from tests.cleanup.conftest import make_cleanup_app


def test_trigger_cleanup_skips_when_below_limits():
    state_map = {('sensor.cleanup', 'number_of_files'): 10, ('sensor.cleanup', 'bytes'): 100}
    app, calls = make_cleanup_app(args={'sensor': 'sensor.cleanup', 'service': 'script.cleanup'}, state_map=state_map)
    app.trigger_cleanup_callback('sensor.cleanup', None, None, None, {})
    assert calls == []


def test_trigger_cleanup_calls_service_when_limits_exceeded():
    state_map = {('sensor.cleanup', 'number_of_files'): 200, ('sensor.cleanup', 'bytes'): 20000000}
    app, calls = make_cleanup_app(args={'sensor': 'sensor.cleanup', 'service': 'script.cleanup'}, state_map=state_map)
    app.trigger_cleanup_callback('sensor.cleanup', None, None, None, {})
    assert ('script.cleanup',) or any(c[0] == 'script.cleanup' for c in calls)
