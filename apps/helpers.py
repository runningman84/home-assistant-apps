"""Small test helpers shared across test files.

Contains a minimal FakeHass class used to satisfy imports from
`appdaemon.plugins.hass.hassapi` during tests.
"""


def _fake_log(self, message, level="INFO", *args, ascii_encode=True, **kwargs):
    # no-op log for tests
    return None


def _fake_now_is_between(self, start, end):
    # default behavior; tests will usually monkeypatch this
    return False


class FakeHass:
    """Minimal replacement for AppDaemon's Hass base class used in tests."""

    def log(self, message, level="INFO", *args, **kwargs):
        return _fake_log(self, message, level, *args, **kwargs)

    def now_is_between(self, start, end):
        return _fake_now_is_between(self, start, end)
