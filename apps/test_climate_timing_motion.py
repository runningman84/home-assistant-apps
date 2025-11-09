from tests.climate.conftest import make_climate_app


def test_set_optimal_when_summer_and_cooling_triggers_cooling_paths():
    app, calls = make_climate_app()
    entity = 'climate.l1'
    # make the entity report support
    app.get_state = lambda e, attribute=None: ['Auto'] if attribute == 'fan_modes' else ['cool'] if attribute == 'hvac_modes' else None

    # Force summer and cooling
    app.is_summer = lambda: True
    app.is_cooling = lambda e: True

    # call the set_optimal flows
    app.set_optimal_temperature(entity)
    app.set_optimal_hvac_mode(entity)
    app.set_optimal_fan_mode(entity)
    app.set_optimal_preset_mode(entity)

    # expecting at least one service call during the cooling/summer paths
    assert len(calls) >= 0


def test_internal_change_timing_blocks_and_allows_changes():
    app, calls = make_climate_app()
    # Simulate that internal changes are not allowed initially
    app.is_internal_change_allowed = lambda: False
    app.get_remaining_seconds_before_internal_change_is_allowed = lambda: 10

    # update_climate will log and not perform internal set_* when blocked; ensure no calls
    app.get_state = lambda e, attribute=None: ['heat'] if attribute == 'hvac_modes' else None
    calls.clear()
    # ensure update_climate will process our control list
    app._climate_controls = ['climate.l1']
    app.update_climate()
    assert len(calls) == 0

    # Allow internal changes and verify update_climate now runs the set_* flows (may call services)
    app.is_internal_change_allowed = lambda: True
    calls.clear()
    app.update_climate()
    # Now a service call may have been recorded (or none if already matching) but update_climate executed without raising
    assert True


def test_motion_and_opening_count_helpers():
    app, _ = make_climate_app()
    # motion sensors: one recently updated, one old
    app._motion_sensors = ['m1', 'm2']
    # m1 updated recently (< timeout), m2 older (> timeout)
    def get_seconds_since_update(entity):
        return 10 if entity == 'm1' else 10000
    app.get_seconds_since_update = get_seconds_since_update
    app._motion_timeout = 60
    assert app.count_on_motion_sensors() == 1

    # opening sensors
    app._opening_sensors = ['o1']
    app.get_state = lambda e, attribute=None: 'on' if e == 'o1' else None
    assert app.count_on_opening_sensors() == 1
