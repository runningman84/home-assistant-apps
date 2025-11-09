def make_weather_app(args=None, state_map=None):
    args = args or {}
    state_map = state_map or {}
    from apps.weather import WeatherWarning
    app = object.__new__(WeatherWarning)
    app.args = args

    app.get_state = lambda e, attribute=None: state_map.get((e, attribute)) if attribute is not None else state_map.get(e)

    calls = []
    app.notify_awtrix = lambda msg, key, ttl, secs: calls.append(('awtrix', msg, key, ttl, secs))
    app.notify_tts = lambda msg: calls.append(('tts', msg))
    app.listen_state = lambda *a, **k: None
    app.run_every = lambda *a, **k: None
    app.log = lambda *a, **k: None

    try:
        app.initialize()
    except Exception:
        pass

    return app, calls
