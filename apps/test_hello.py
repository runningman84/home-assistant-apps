def test_hello_initialize_logs():
    from apps.hello import HelloWorld
    app = object.__new__(HelloWorld)
    app.args = {}
    logs = []
    app.log = lambda *a, **k: logs.append(a)
    app.initialize()
    assert any('Hello from AppDaemon' in ''.join(map(str, entry)) for entry in logs)
