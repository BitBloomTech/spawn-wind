# spawn
# Copyright (C) 2018, Simmovation Ltd.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either fast_version 3 of the License, or
# (at your option) any later fast_version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
from os import path, linesep
import pytest
import tempfile
import pandas as pd
import numpy as np
import math
import luigi
from wetb.fast import fast_io
from spawnwind.nrel import Fast7Input, Fast8Input, TurbsimInput, FastSimulationSpawner, TurbsimSpawner

def run_and_get_results(spawner, path_):
    task = spawner.spawn(str(path_), {})
    luigi.build([task], local_scheduler=True, log_level='WARNING')
    output_path = task.output().path
    if not path.isfile(output_path):
        with open(path.splitext(output_path)[0] + '.log') as fp:
            log = fp.read()
        raise ChildProcessError('FAST run did not produce output. Log:' + linesep + log)
    data, info = fast_io.load_output(output_path)
    return pd.DataFrame(data, columns=info['attribute_names'])

def _create_spawner(tmpdir, turbsim_input_file, fast_input_file, fast_input_cls):
    turbsim_input = TurbsimInput.from_file(turbsim_input_file)
    wind_spawner = TurbsimSpawner(turbsim_input)
    fast_input = fast_input_cls.from_file(fast_input_file)
    spawner = FastSimulationSpawner(fast_input, wind_spawner, tmpdir)
    spawner.wind_speed = 8.0
    spawner.output_start_time = 0.0
    spawner.simulation_time = 1.0
    return spawner

@pytest.fixture(scope='function')
def spawner(fast_version, tmpdir, turbsim_input_file, fast_input_file):
    if fast_version == 'v7':
        return _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast7Input)
    elif fast_version == 'v8':
        return _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast8Input)


@pytest.fixture(scope='module')
def baseline(fast_version, turbsim_input_file, fast_input_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        if fast_version == 'v7':
            s = _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast7Input)
        elif fast_version == 'v8':
            s = _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast8Input)
        return run_and_get_results(s, tmpdir)

@pytest.fixture(scope='module')
def turbulent_baseline(fast_version, turbsim_input_file, fast_input_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        if fast_version == 'v7':
            s = _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast7Input)
        elif fast_version == 'v8':
            s = _create_spawner(tmpdir, turbsim_input_file, fast_input_file, Fast8Input)
        s.wind_type = 'bladed'
        return run_and_get_results(s, tmpdir)

@pytest.fixture
def wind_keys(fast_version):
    if fast_version == 'v7':
        return {
            'longitudinal': 'WindVxi',
            'vertical': 'WindVzi'
        }
    elif fast_version == 'v8':
        return {
            'longitudinal': 'Wind1VelX',
            'vertical': 'Wind1VelZ'
        }

@pytest.mark.parametrize('property,type', [
    ('output_start_time', float),
    ('simulation_time', float),
    ('wind_speed', float),
    ('turbulence_intensity', float),
    ('turbulence_seed', int),
    ('wind_shear', float),
    ('upflow', float),
    ('initial_rotor_speed', float),
    ('initial_azimuth', float),
    ('initial_yaw', float),
    ('pitch_control_start_time', float),
    ('yaw_manoeuvre_time', float),
    ('final_yaw', float),
    ('wake_model_on', bool),
    ('dynamic_stall_on', bool),
    ('number_of_blades', int)
])
def test_property_type(spawner, property, type):
    assert isinstance(getattr(spawner, property), type)


@pytest.mark.skipif('sys.platform != "win32"')
def test_output_start_time(spawner, tmpdir):
    spawner.output_start_time = 0.5
    res = run_and_get_results(spawner, tmpdir)
    assert res['Time'][0] == pytest.approx(0.5)
    assert res['Time'].iloc[-1] - res['Time'][0] == pytest.approx(spawner.simulation_time)


@pytest.mark.skipif('sys.platform != "win32"')
def test_simulation_time(spawner, tmpdir):
    spawner.output_start_time = 1.0
    spawner.simulation_time = 2.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['Time'].iloc[-1] - res['Time'][0] == pytest.approx(spawner.simulation_time)


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('key,value,output_name', [
    ('initial_rotor_speed', 7.0, 'RotSpeed'),
    ('initial_azimuth', 180.0, 'Azimuth'),
    ('initial_yaw', 10.0, 'YawPzn'),
    ('initial_pitch', 30.0, 'BldPitch1')
])
def test_initial_values(spawner, key, value, output_name, tmpdir):
    setattr(spawner, key, value)
    res = run_and_get_results(spawner, tmpdir)
    assert res[output_name][0] == pytest.approx(value, rel=0.1)


@pytest.mark.parametrize('key,index,value', [
    ('blade_initial_pitch', 1, 10.0),
    ('blade_pitch_manoeuvre_time', 2, 30.0),
    ('blade_final_pitch', 3, 90.0)
])
def test_set_and_then_get_indexed_parameters(spawner, key, index, value):
    array = getattr(spawner, key)
    array[index] = value
    retval = array[index]
    assert retval == value


@pytest.mark.skipif('sys.platform != "win32"')
def test_operating_mode(spawner, tmpdir):
    spawner.initial_pitch = 30.0
    spawner.operation_mode = 'idling'
    res = run_and_get_results(spawner, path.join(tmpdir, 'a'))
    assert np.all(res['BldPitch1'] == 30.0)
    assert np.all(res['GenPwr'] <= 0.0)
    assert np.all(res['RotSpeed'][1:] != 0.0)
    assert np.all(abs(res['RotSpeed']) < 1.0)
    spawner.operation_mode = 'parked'
    spawner.initial_pitch = 90.0
    res2 = run_and_get_results(spawner, path.join(tmpdir, 'b'))
    assert np.all(res2['BldPitch1'] == 90.0)
    assert np.all(res2['GenPwr'] <= 0.0)
    assert np.all(abs(res2['RotSpeed']) <= 0.011)    # rotor speed is slightly non-zero due to drive-train flexibility
    spawner.operation_mode = 'normal'
    spawner.initial_pitch = 0.0
    res3 = run_and_get_results(spawner, path.join(tmpdir, 'c'))
    assert np.all(res3['BldPitch1'] <= 10.0)
    assert np.all(res3['GenPwr'] >= 0.0)
    assert np.all(res3['RotSpeed'][1:] > 0.0)  # initial rotor speed = 0, so ignore first time step


@pytest.mark.skipif('sys.platform != "win32"')
def test_pitch_manoeuvre_all_blades(spawner, tmpdir):
    spawner.simulation_time = 5.0
    spawner.initial_pitch = 10.0
    spawner.final_pitch = 12.0
    spawner.pitch_manoeuvre_time = 1.0
    spawner.pitch_manoeuvre_rate = 1.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['BldPitch1'].iloc[-1] == pytest.approx(12.0)


@pytest.mark.skipif('sys.platform != "win32"')
def test_pitch_manoeuvre_one_blade(spawner, tmpdir):
    spawner.simulation_time = 5.0
    spawner.initial_pitch = 10.0
    spawner.blade_final_pitch[1] = 12.0
    spawner.blade_final_pitch[2] = 10.0
    spawner.blade_final_pitch[3] = 10.0
    spawner.pitch_manoeuvre_time = 1.0
    spawner.pitch_manoeuvre_rate = 1.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['BldPitch1'].iloc[-1] == pytest.approx(12.0)


@pytest.mark.skipif('sys.platform != "win32"')
def test_pitch_control_start_time(spawner, tmpdir):
    spawner.simulation_time = 10.0
    spawner.wind_speed = 16.0
    spawner.pitch_control_start_time = 1.0
    res = run_and_get_results(spawner, tmpdir)
    pitch = np.array(res['BldPitch1'].values)
    assert np.std(pitch[:9]) == 0.0
    assert np.std(pitch[10:]) > 0.0


from matplotlib import pyplot

@pytest.mark.skipif('sys.platform != "win32"')
def test_yaw_manoeuvre(spawner, tmpdir):
    spawner.simulation_time = 4.0
    spawner.initial_yaw = 0.0
    spawner.final_yaw = 1.5
    spawner.yaw_manoeuvre_time = 0.5
    spawner.yaw_manoeuvre_rate = 0.8
    res = run_and_get_results(spawner, tmpdir)
    assert res['YawPzn'].iloc[0] == pytest.approx(0.0, abs=0.001)
    assert res['YawPzn'].iloc[-1] == pytest.approx(1.5, abs=0.01)


@pytest.mark.skipif('sys.platform != "win32"')
def test_grid_loss(spawner, tmpdir):
    spawner.simulation_time = 2.0
    spawner.grid_loss_time = 1.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['GenPwr'].iloc[-1] == 0.0
    assert res['GenTq'].iloc[-1] == 0.0

turb_wind_types = ['bladed', 'turbsim']

@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_turbulence_seed(turbulent_baseline, spawner, tmpdir, wind_keys, wind_type):
    spawner.wind_type = wind_type
    spawner.turbulence_seed += 1
    res = run_and_get_results(spawner, tmpdir)
    assert np.all(turbulent_baseline[wind_keys['longitudinal']] != res[wind_keys['longitudinal']])


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_wind_speed(turbulent_baseline, spawner, tmpdir, wind_keys, wind_type):
    spawner.wind_type = wind_type
    spawner.wind_type = 'bladed'
    spawner.wind_speed = 2 * spawner.wind_speed
    res = run_and_get_results(spawner, tmpdir)
    assert np.mean(res[wind_keys['longitudinal']]) == pytest.approx(2*np.mean(turbulent_baseline[wind_keys['longitudinal']]), rel=0.1)


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_turbulence_intensity(turbulent_baseline, spawner, tmpdir, wind_keys, wind_type):
    spawner.wind_type = wind_type
    assert 1.0 < spawner.turbulence_intensity < 100.0
    spawner.turbulence_intensity = 2 * spawner.turbulence_intensity
    res = run_and_get_results(spawner, tmpdir)
    assert np.std(res[wind_keys['longitudinal']]) == pytest.approx(2*np.std(turbulent_baseline[wind_keys['longitudinal']]), rel=1e-3)


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_turbulence_seed(turbulent_baseline, spawner, tmpdir, wind_keys, wind_type):
    spawner.wind_type = wind_type
    spawner.turbulence_seed += 1
    res = run_and_get_results(spawner, tmpdir)
    assert np.all(turbulent_baseline[wind_keys['longitudinal']] != res[wind_keys['longitudinal']])


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_wind_shear(turbulent_baseline, spawner, tmpdir, wind_type):
    spawner.wind_type = wind_type
    spawner.wind_shear = 0.3
    res = run_and_get_results(spawner, tmpdir)
    # increase in shear gives predominantly 0P increase in tower-top overturning moment
    # first few time steps sometimes don't match the overall trend so ignore them
    assert np.all((res['YawBrMyp'] > turbulent_baseline['YawBrMyp'])[5:])


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize('wind_type', turb_wind_types)
def test_upflow(turbulent_baseline, spawner, tmpdir, wind_keys, wind_type):
    spawner.wind_type = wind_type
    spawner.upflow = 10.0
    res = run_and_get_results(spawner, tmpdir)
    assert np.mean(res[wind_keys['longitudinal']]) < np.mean(turbulent_baseline[wind_keys['longitudinal']])
    upflow_baseline = np.mean(np.arctan2(turbulent_baseline[wind_keys['vertical']], turbulent_baseline[wind_keys['longitudinal']]))
    upflow_new = np.mean(np.arctan2(res[wind_keys['vertical']], res[wind_keys['longitudinal']]))
    assert math.degrees(upflow_new - upflow_baseline) == pytest.approx(spawner.upflow, abs=0.1)


@pytest.mark.skipif('sys.platform != "win32"')
def test_fails_with_invalid_wind_file(spawner, tmpdir):
    spawner.wind_file = 'C:/this/is/a/bad/path.wnd'
    task = spawner.spawn(str(tmpdir), {})
    with pytest.raises(ChildProcessError):
        task.run()


@pytest.mark.skipif('sys.platform != "win32"')
def test_completes_with_relative_wind_file(spawner, tmpdir):
    # This test must be run with root as working directory
    spawner.wind_file = 'example_data/fast_input_files/wind_files/NWP4.0.wnd'
    task = spawner.spawn(str(tmpdir), {})
    task.run()
    assert task.complete()


@pytest.mark.skipif('sys.platform != "win32"')
def test_runaway_at_high_wind_speed(spawner, tmpdir):
    spawner.wind_speed = 24.0
    spawner.simulation_time = 20.0
    spawner.pitch_manoeuvre_rate = 6.0
    spawner.pitch_manoeuvre_time = 1.0
    spawner.set_blade_final_pitch(1, 90.0)
    res = run_and_get_results(spawner, tmpdir)
    assert res['BldPitch1'].iloc[-1] == pytest.approx(90.0)


@pytest.mark.skipif('sys.platform != "win32"')
def test_turn_off_dynamic_stall(spawner, tmpdir):
    spawner.simulation_time = 2.0
    spawner.dynamic_stall_on = False
    run_and_get_results(spawner, tmpdir)


@pytest.mark.skipif('sys.platform != "win32"')
def test_turn_off_wake_model(spawner, tmpdir):
    spawner.simulation_time = 2.0
    spawner.wake_model_on = False
    run_and_get_results(spawner, tmpdir)
