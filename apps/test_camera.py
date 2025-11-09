from tests.camera.conftest import make_camera_app


def test_get_next_run_and_process_and_start_stop():
    app, calls = make_camera_app(args={'sensors': ['s1'], 'image_processor': 'img.proc'})

    # set processing_count and verify intervals
    app._processing_count = 50
    assert app.get_next_run_in_sec() in (2,)

    # process_image should call service and schedule run_in
    app._image_processor = 'img.proc'
    calls.clear()
    app._processing_max_count = 2
    app.process_image({})
    assert any(c[0] == 'image_processing/scan' for c in calls)

    # start_image_processing should schedule and reset count
    calls.clear()
    app.start_image_processing()
    assert app._processing_count == 0
    assert app._processing_handle is not None

    # stop should cancel and set count to max
    calls.clear()
    app.stop_image_processing()
    assert any(c[0] == 'cancel' for c in calls) or app._processing_handle is None

def test_count_sensors_and_stop_behavior():
    app, calls = make_camera_app(args={'sensors': ['s1', 's2']})
    # no sensors on -> count_on_sensors == 0 -> stop_image_processing called
    app.get_state = lambda e, attribute=None: 'off'

    # attach a spy to stop_image_processing
    called = {}
    app.stop_image_processing = lambda: called.setdefault('stopped', True)

    # simulate stop callback from sensor off
    app.trigger_stop_image_scan_callback('s1', 'state', 'on', 'off', {})
    assert called.get('stopped', False) is True

    # when sensors still on, stop should not be called
    app.get_state = lambda e, attribute=None: 'on' if e == 's2' else 'off'
    called.clear()
    app.trigger_stop_image_scan_callback('s1', 'state', 'on', 'off', {})
    assert called == {}
