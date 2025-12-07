import random


def make_welcome_app():
    from apps.welcome import WelcomeControl

    app = object.__new__(WelcomeControl)
    # minimal base attributes expected by methods
    app._name_mapping = {"Markus": "Mark-oos"}
    app._device_trackers = ["device_tracker.phone_markus", "device_tracker.phone_anna"]
    app._resident_timeout = 300
    app._language = "english"
    app._translation = {
        "english": {
            "welcome_with_name": ["Welcome back {names}!"],
            "welcome_no_name": ["Welcome!"],
            "farewell_with_name": ["Goodbye {names}!"],
            "farewell_no_name": ["Goodbye!"]
        }
    }
    return app


def test_format_name_list_variants():
    app = make_welcome_app()
    # stub get_state to return friendly names
    app.get_state = lambda e, attribute=None: "Markus Müller" if "markus" in e else "Anna Schmidt"

    assert app._format_name_list([], mapped=True) == ""
    assert app._format_name_list(["device_tracker.phone_markus"], mapped=False) == "Markus"
    assert app._format_name_list(["device_tracker.phone_markus", "device_tracker.phone_anna"], mapped=False) == "Markus und Anna"
    assert ", " in app._format_name_list(["device_tracker.phone_markus", "device_tracker.phone_anna", "device_tracker.phone_markus"], mapped=False)


def test_select_template_and_parity():
    app = make_welcome_app()
    # Ensure deterministic random choice
    random.seed(0)
    # With names
    template = app._select_template("welcome", True)
    assert "{names}" in template
    # format with mapped/unmapped names
    app.get_state = lambda e, attribute=None: "Markus Müller" if "markus" in e else "Anna Schmidt"
    audio_names = app._format_name_list(["device_tracker.phone_markus"], mapped=True)
    text_names = app._format_name_list(["device_tracker.phone_markus"], mapped=False)
    audio = template.format(names=audio_names)
    text = template.format(names=text_names)
    assert audio != text


def test_get_residents_time_boundary():
    app = make_welcome_app()
    # stub get_state and get_seconds_since_update to use reference_time
    def get_state(entity, attribute=None):
        if "markus" in entity:
            return "home"
        return "not_home"

    def get_seconds_since_update(entity):
        # return exactly resident_timeout for markus
        if "markus" in entity:
            return float(app._resident_timeout)
        return 1000.0

    app.get_state = get_state
    app.get_seconds_since_update = get_seconds_since_update

    # Using current logic, exactly equal to timeout should be treated as NOT recent (strict <)
    residents = app.get_residents()
    assert residents == []


def test_select_template_language_fallback():
    app = make_welcome_app()
    app._language = "nonexistent"
    # fallback to english should still return a template
    tpl = app._select_template("welcome", False)
    assert isinstance(tpl, str)
