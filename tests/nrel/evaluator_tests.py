import pytest
from spawnwind.nrel.plugin import NTM, ETM, ApproxInitialPitch, ApproxInitialRotorSpeed


@pytest.mark.parametrize('Iref,wind_speed', [
    (12.0, 2.0),
    (12.0, 11.0),
    (16.0, 7.0),
    (16.0, 9.0),
])
def test_extreme_model_has_higher_turbulence_than_normal_model(Iref, wind_speed):
    assert ETM(Iref, 8.0, wind_speed) > NTM(Iref, wind_speed)


def test_turbulence_models_have_lower_turbulence_at_higher_wind_speeds():
    assert NTM(14.0, 10.0) < NTM(14.0, 5.0)
    assert ETM(14.0, 7.5, 10.0) < ETM(14.0, 7.5, 5.0)


def test_initial_rotor_speed():
    omega_rated = 8.0
    ws_rated = 9.0
    assert ApproxInitialRotorSpeed(omega_rated, ws_rated, 0.0) == 0.0
    assert ApproxInitialRotorSpeed(omega_rated, ws_rated, ws_rated/2) == pytest.approx(omega_rated / 2)
    assert ApproxInitialRotorSpeed(omega_rated, ws_rated, ws_rated) == pytest.approx(omega_rated)
    assert ApproxInitialRotorSpeed(omega_rated, ws_rated, 2 * ws_rated) == omega_rated


def test_initial_pitch():
    omega_rated = 8.0
    ws_rated = 11.0
    fine_pitch = 0.0
    coeff = 6.0
    assert ApproxInitialPitch(ws_rated, fine_pitch, coeff, ws_rated/2) == 0.0
    assert ApproxInitialPitch(ws_rated, fine_pitch, coeff, ws_rated) == pytest.approx(0.0)
    assert 0.0 < ApproxInitialPitch(ws_rated, fine_pitch, coeff, 2 * ws_rated) < 90.0
