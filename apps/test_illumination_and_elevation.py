from tests.light.conftest import make_light_app


def test_below_min_elevation_and_illumination_missing_unknown():
    app, calls = make_light_app(args={'illumination_sensors': ['sensor.l1'], 'min_elevation': 10})
    # elevation below threshold
    app.get_state = lambda e, attribute=None: 5 if e == 'sun.sun' and attribute == 'elevation' else None
    app._min_elevation = 10
    assert app.below_min_elevation() is True

    # illumination sensor missing -> below_min_illumination True
    app._illumination_sensors = ['sensor.l1']
    app.get_state = lambda e, attribute=None: None
    assert app.below_min_illumination() is True

    # unknown/unavailable treated as below threshold
    app.get_state = lambda e, attribute=None: 'unknown'
    assert app.below_min_illumination() is True


def test_above_max_illumination_false_on_missing_values_and_true_on_high():
    app, calls = make_light_app()
    app._illumination_sensors = ['sensor.l1']
    # missing returns False
    app.get_state = lambda e, attribute=None: None
    assert app.above_max_illumination() is False

    # high value triggers True
    app.get_state = lambda e, attribute=None: '999'
    app._max_illumination = 150
    assert app.above_max_illumination() is True
