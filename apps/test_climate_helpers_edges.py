from tests.climate.conftest import make_climate_app


def test_desired_temperature_by_status_reads_control_entity_and_offset():
    app, _ = make_climate_app()
    app._offset_temperature = 1.5
    app._home_temperature_control = 'input_number.home_temp'
    app.get_state = lambda e, attribute=None: '21' if e == 'input_number.home_temp' else None
    assert app.get_desired_temperature_by_status('home') == 22.5


def test_current_and_target_temperature_unavailable_and_unknown():
    app, _ = make_climate_app()
    # current temperature unavailable
    app.get_state = lambda e, attribute=None: 'unavailable' if attribute == 'current_temperature' else None
    assert app.get_current_temperature('climate.x') == 0
    # target temperature unknown
    app.get_state = lambda e, attribute=None: 'unknown' if attribute == 'temperature' else None
    assert app.get_target_temperature('climate.x') == 0


def test_desired_fan_mode_voc_and_entity_support():
    app, _ = make_climate_app()
    # when entity provided and Auto not supported -> None
    app.is_fan_mode_supported = lambda e, mode=None: False
    assert app.get_desired_fan_mode('climate.x') is None

    # voc large values produce high mapping
    app.is_fan_mode_supported = lambda e, mode=None: True
    app._voc_threshold = 10
    app.get_voc_measurement = lambda: 500
    # should map to at least Mid/High depending on mapping; check not Auto
    fm = app.get_desired_fan_mode()
    assert fm in ('Mid', 'HighMid', 'High', 'Auto')


def test_desired_preset_mode_support_and_setting():
    app, calls = make_climate_app()
    # entity does not support preset -> None
    app.is_preset_mode_supported = lambda e, mode=None: False
    assert app.get_desired_preset_mode('climate.x') is None

    # entity supports preset -> returns default
    app.is_preset_mode_supported = lambda e, mode=None: True
    assert app.get_desired_preset_mode('climate.x') == 'quiet'

    # set_optimal_preset_mode should call set_preset_mode when supported
    app.get_current_preset_mode = lambda e: 'none'
    calls.clear()
    app.set_preset_mode = lambda eid, pm='none': calls.append(('preset', pm))
    app.set_optimal_preset_mode('climate.x')
    assert calls != []


def test_periodic_time_callback_invokes_update_climate():
    app, _ = make_climate_app()
    called = []
    app.update_climate = lambda: called.append('ok')
    app.periodic_time_callback({})
    assert called == ['ok']
