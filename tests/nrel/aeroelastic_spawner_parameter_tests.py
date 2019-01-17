# spawn
# Copyright (C) 2018, Simmovation Ltd.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
from os import path
import pytest
import tempfile
import pandas as pd
import numpy as np
import math
import luigi
from wetb.fast import fast_io
from spawnwind.nrel import FastInput, TurbsimInput, FastSimulationSpawner, TurbsimSpawner

def run_and_get_results(spawner, path_):
    task = spawner.spawn(str(path_), {})
    luigi.build([task], local_scheduler=True, log_level='WARNING')
    data, info = fast_io.load_output(task.output().path)
    return pd.DataFrame(data, columns=info['attribute_names'])

def _create_spawner(tmpdir, turbsim_input_file, fast_input_file):
    turbsim_input = TurbsimInput.from_file(turbsim_input_file)
    wind_spawner = TurbsimSpawner(turbsim_input)
    fast_input = FastInput.from_file(fast_input_file)
    spawner = FastSimulationSpawner(fast_input, wind_spawner, tmpdir)
    spawner.wind_speed = 8.0
    spawner.output_start_time = 0.0
    spawner.simulation_time = 1.0
    return spawner


@pytest.fixture()
def spawner(tmpdir, turbsim_input_file, fast_input_file):
    return _create_spawner(tmpdir, turbsim_input_file, fast_input_file)


@pytest.fixture(scope='module')
def baseline(turbsim_input_file, fast_input_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        s = _create_spawner(tmpdir, turbsim_input_file, fast_input_file)
        return run_and_get_results(s, tmpdir)


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
    ('number_of_blades', int)
])
def test_property_type(spawner, property, type):
    assert isinstance(getattr(spawner, property), type)


@pytest.mark.skipif('sys.platform != "win32"')
def test_output_start_time(baseline, spawner, tmpdir):
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
    ('initial_yaw', 90.0, 'YawPzn'),
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
    spawner.operation_mode = 'idling'
    spawner.initial_pitch = 30.0
    res = run_and_get_results(spawner, path.join(tmpdir, 'a'))
    assert np.all(res['BldPitch1'] == 30.0)
    assert np.all(res['GenPwr'] <= 0.0)
    assert np.all(res['RotSpeed'] != 0.0)
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
    assert np.all(res3['RotSpeed'] > 0.0)


@pytest.mark.skipif('sys.platform != "win32"')
def test_pitch_manoeuvre_all_blades(spawner, tmpdir):
    spawner.simulation_time = 4.0
    spawner.initial_pitch = 10.0
    spawner.final_pitch = 12.0
    spawner.pitch_manoeuvre_time = 1.0
    spawner.pitch_manoeuvre_rate = 1.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['BldPitch1'].iloc[-1] == pytest.approx(12.0)


@pytest.mark.skipif('sys.platform != "win32"')
def test_pitch_manoeuvre_one_blade(spawner, tmpdir):
    spawner.simulation_time = 4.0
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
    spawner.simulation_time = 2.0
    spawner.wind_speed = 16.0
    spawner.pitch_control_start_time = 1.0
    res = run_and_get_results(spawner, tmpdir)
    pitch = np.array(res['BldPitch1'].values)
    assert np.std(pitch[:9]) == 0.0
    assert np.std(pitch[10:]) > 0.0


@pytest.mark.skipif('sys.platform != "win32"')
def test_yaw_manoeuvre(spawner, tmpdir):
    spawner.simulation_time = 4.0
    spawner.initial_yaw = 5.0
    spawner.final_yaw = 6.5
    spawner.yaw_manoeuvre_time = 0.5
    spawner.yaw_manoeuvre_rate = 0.8
    res = run_and_get_results(spawner, tmpdir)
    assert res['YawPzn'].iloc[0] == pytest.approx(5.0)
    assert res['YawPzn'].iloc[-1] == pytest.approx(6.5)


@pytest.mark.skipif('sys.platform != "win32"')
def test_grid_loss(spawner, tmpdir):
    spawner.simulation_time = 2.0
    spawner.grid_loss_time = 1.0
    res = run_and_get_results(spawner, tmpdir)
    assert res['GenPwr'].iloc[-1] == 0.0
    assert res['GenTq'].iloc[-1] == 0.0


@pytest.mark.skipif('sys.platform != "win32"')
def test_turbulence_seed(baseline, spawner, tmpdir):
    spawner.turbulence_seed += 1
    res = run_and_get_results(spawner, tmpdir)
    assert np.all(baseline['WindVxi'] != res['WindVxi'])


@pytest.mark.skipif('sys.platform != "win32"')
def test_wind_speed(baseline, spawner, tmpdir):
    spawner.wind_speed = 2 * spawner.wind_speed
    res = run_and_get_results(spawner, tmpdir)
    assert np.mean(res['WindVxi']) == pytest.approx(2*np.mean(baseline['WindVxi']), rel=0.1)


@pytest.mark.skipif('sys.platform != "win32"')
def test_turbulence_intensity(baseline, spawner, tmpdir):
    assert 1.0 < spawner.turbulence_intensity < 100.0
    spawner.turbulence_intensity = 2 * spawner.turbulence_intensity
    res = run_and_get_results(spawner, tmpdir)
    assert np.std(res['WindVxi']) == pytest.approx(2*np.std(baseline['WindVxi']), rel=1e-3)


@pytest.mark.skipif('sys.platform != "win32"')
def test_turbulence_seed(baseline, spawner, tmpdir):
    spawner.turbulence_seed += 1
    res = run_and_get_results(spawner, tmpdir)
    assert np.all(baseline['WindVxi'] != res['WindVxi'])


@pytest.mark.skipif('sys.platform != "win32"')
def test_wind_shear(baseline, spawner, tmpdir):
    spawner.wind_shear = 0.3
    res = run_and_get_results(spawner, tmpdir)
    assert np.all(res['YawBrMyp'] > baseline['YawBrMyp'])  # increase in shear gives predominantly 0P increase in tower-top overturning moment


@pytest.mark.skipif('sys.platform != "win32"')
def test_upflow(baseline, spawner, tmpdir):
    spawner.upflow = 10.0
    res = run_and_get_results(spawner, tmpdir)
    assert np.mean(res['WindVxi']) < np.mean(baseline['WindVxi'])
    upflow_baseline = np.mean(np.arctan2(baseline['WindVzi'], baseline['WindVxi']))
    upflow_new = np.mean(np.arctan2(res['WindVzi'], res['WindVxi']))
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
