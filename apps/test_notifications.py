from tests.base.factories import make_base_app
import json


def test_notify_awtrix_and_reset_builds_json_and_calls_mqtt():
    app = make_base_app()

    # send notification
    app.notify_awtrix("hello world", app="TestApp", duration=5, lifetime=10)

    # reset
    app.reset_awtrix(app="TestApp")

    # validate mqtt publish calls
    publishes = [c for c in app._called["services"] if c[0] == "mqtt/publish"]
    assert len(publishes) == 2

    # first payload should be JSON with text and duration
    topic1, kwargs1 = publishes[0]
    assert kwargs1["topic"] == "awtrix_prefix/custom/TestApp"
    payload1 = json.loads(kwargs1.get("payload")) if isinstance(kwargs1.get("payload"), str) else {}
    assert payload1.get("text") == "hello world"
    assert payload1.get("duration") == 5

    # second payload is the reset (empty object)
    topic2, kwargs2 = publishes[1]
    assert kwargs2["topic"] == "awtrix_prefix/custom/TestApp"
    payload2 = json.loads(kwargs2.get("payload")) if isinstance(kwargs2.get("payload"), str) else None
    assert payload2 == {}


def test_notify_media_and_tts_and_alexa_called():
    app = make_base_app()

    app.notify_media(message="Test Message", title="Title")

    # verify services called: alexa, monkey, tts device volume and tts speak
    services = [s[0] for s in app._called["services"]]
    assert "notify/alexa_media" in services
    assert "rest_command/trigger_monkey" in services
    # volume_set and tts/speak are called for each media player
    assert any(s[0] == "media_player/volume_set" for s in app._called["services"]) or any(s[0] == "tts/speak" for s in app._called["services"]) 


def test_notify_respects_night_window_for_media():
    app = make_base_app()

    # now_is_between returns True for our stub, so notify should skip media when prio > 0
    app.notify("night message", prio=1)

    # media calls should not be present because night and prio > 0
    services = [s[0] for s in app._called["services"]]
    assert "tts/speak" not in services

def test_notify_awtrix_sends_mqtt_with_default_app_and_prefix(make_base_app, monkeypatch):
    """notify_awtrix should publish an MQTT message to each configured prefix
    using the default app name (class name) and default duration/lifetime.
    """
    app = make_base_app()

    app._awtrix_prefixes = ["prefix1"]

    calls = []

    def fake_call_service(service, **kwargs):
        calls.append((service, kwargs))

    # attach call_service directly to the app instance
    app.call_service = fake_call_service

    app.notify_awtrix("hello world")

    # one mqtt publish call
    assert len(calls) == 1
    service, kwargs = calls[0]
    assert service == 'mqtt/publish'
    assert kwargs.get('topic') == 'prefix1/custom/BaseApp'

    payload = json.loads(kwargs.get('payload'))
    assert payload['text'] == 'hello world'
    assert payload.get('rainbow') is True
    assert payload.get('duration') == 60
    assert payload.get('lifetime') == 600


def test_notify_awtrix_with_app_name_and_multiple_prefixes(make_base_app, monkeypatch):
    """notify_awtrix should use the provided app name and publish to all prefixes."""
    app = make_base_app()

    app._awtrix_prefixes = ["p1", "p2"]

    calls = []

    def fake_call_service(service, **kwargs):
        calls.append((service, kwargs))

    # attach call_service directly to the app instance
    app.call_service = fake_call_service

    app.notify_awtrix("ping", app="MyApp", duration=5, lifetime=30)

    # Expect two mqtt publish calls, one per prefix
    assert len(calls) == 2

    topics = {kwargs.get('topic') for (_s, kwargs) in calls}
    assert topics == {"p1/custom/MyApp", "p2/custom/MyApp"}

    # Verify payload content for each call
    for (_s, kwargs) in calls:
        payload = json.loads(kwargs.get('payload'))
        assert payload['text'] == 'ping'
        assert payload.get('duration') == 5
        assert payload.get('lifetime') == 30



def test_notify_suppresses_media_at_night_for_low_prio(make_base_app, monkeypatch):
    """Low priority notifications (prio > 0) should not trigger media output during night."""
    app = make_base_app()

    # Force night time
    monkeypatch.setattr(app, "is_time_in_night_window", lambda: True)

    # initialize attributes used by notify to avoid AttributeError
    app._telegram_user_ids = []
    app._notify_targets = []
    app._alexa_media_devices = []
    app._alexa_monkeys = []
    app._tts_devices = []
    app._silent_control = None
    # stub out services used by notify
    app.call_service = lambda *a, **k: None

    called = {"tts": 0, "alexa": 0}

    def fake_notify_tts(message, title=None, volume_level=0.35):
        called["tts"] += 1

    def fake_notify_alexa_media(message, title=None):
        called["alexa"] += 1

    monkeypatch.setattr(app, "notify_tts", fake_notify_tts)
    monkeypatch.setattr(app, "notify_alexa_media", fake_notify_alexa_media)

    # call notify with normal priority (1)
    app.notify("hello at night", prio=1)

    # media helpers should NOT be called at night for prio > 0
    assert called["tts"] == 0
    assert called["alexa"] == 0


def test_notify_allows_media_at_night_for_urgent_prio(make_base_app, monkeypatch):
    """Urgent notifications (prio == 0) must still trigger media output even at night."""
    app = make_base_app()

    # Force night time
    monkeypatch.setattr(app, "is_time_in_night_window", lambda: True)

    # initialize attributes used by notify to avoid AttributeError
    app._telegram_user_ids = []
    app._notify_targets = []
    app._alexa_media_devices = []
    app._alexa_monkeys = []
    app._tts_devices = []
    app._silent_control = None
    # stub out services used by notify
    app.call_service = lambda *a, **k: None

    called = {"tts": 0, "alexa": 0}

    def fake_notify_tts(message, title=None, volume_level=0.35):
        called["tts"] += 1

    def fake_notify_alexa_media(message, title=None):
        called["alexa"] += 1

    monkeypatch.setattr(app, "notify_tts", fake_notify_tts)
    monkeypatch.setattr(app, "notify_alexa_media", fake_notify_alexa_media)

    # call notify with urgent priority (0)
    app.notify("urgent at night", prio=0)

    # media helpers should be called for urgent prio
    assert called["tts"] >= 1
    assert called["alexa"] >= 1
