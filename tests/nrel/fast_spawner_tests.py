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
import tempfile
import pytest
from spawn.config.command_line import CommandLineConfiguration
from spawn.schedulers.luigi import LuigiScheduler
from spawn.parsers import SpecificationParser, DictSpecificationProvider

from spawnwind.nrel import TurbsimSpawner, FastSimulationSpawner, FastInput, TurbsimInput, WindGenerationTask

@pytest.fixture(scope='function')
def turbsim_input(examples_folder):
    return TurbsimInput.from_file(path.join(examples_folder, 'TurbSim.inp'))


@pytest.fixture(scope='function')
def fast_input(examples_folder):
    return FastInput.from_file(path.join(examples_folder, 'NRELOffshrBsline5MW_Onshore.fst'))


@pytest.mark.skipif('sys.platform != "win32"')
def test_can_spawn_turbsim_task(turbsim_input):
    temp_dir = tempfile.TemporaryDirectory()
    spawner = TurbsimSpawner(turbsim_input)
    task = spawner.spawn(temp_dir.name, {})
    assert len(task.requires()) == 0
    assert task.wind_file_path == path.join(temp_dir.name, 'wind.wnd')
    assert not task.complete()


@pytest.mark.skipif('sys.platform != "win32"')
def test_spawns_tests_requiring_wind_generation_when_wind_changed(turbsim_input, fast_input):
    temp_dir = tempfile.TemporaryDirectory()
    spawner = FastSimulationSpawner(fast_input, TurbsimSpawner(turbsim_input), temp_dir.name)
    task = spawner.spawn(path.join(temp_dir.name, 'a'), {})
    s2 = spawner.branch()
    s2.wind_speed = 8.0
    task2 = s2.spawn(path.join(temp_dir.name, 'b'), {})
    assert isinstance(task2.requires()[0], WindGenerationTask)
    s2.initial_yaw = 10.0
    task3 = s2.spawn(path.join(temp_dir.name, 'c'), {})
    assert task2.requires()[0]._id != task.requires()[0]._id
    assert task3.requires()[0]._id == task2.requires()[0]._id


def test_spawn_with_additional_directory_puts_tasks_in_new_folders(turbsim_input, fast_input, tmpdir):
    runs_dir_1 = path.join(tmpdir, 'runs', '1')
    runs_dir_2 = path.join(tmpdir, 'runs', '2')
    spawner = FastSimulationSpawner(fast_input, TurbsimSpawner(turbsim_input), tmpdir)
    spawner.wind_speed = 6.0
    task1 = spawner.spawn(runs_dir_1, {})
    spawner.wind_speed = 8.0
    task2 = spawner.spawn(runs_dir_2, {})
    assert task1.output().path != task2.output().path
    assert task1.requires()[0].output().path != task2.requires()[0].output().path


@pytest.mark.skipif('sys.platform != "win32"')
def test_runs_two_tasks_successfully_that_use_same_prerequisite(turbsim_input, fast_input, tmpdir, plugin_loader):
    spawner = FastSimulationSpawner(fast_input, TurbsimSpawner(turbsim_input), tmpdir)
    spec_dict = {
        "spec": {
            "simulation_time": 1.0,
            "wind_speed": 6.0,
            "initial_yaw": [-10.0, 10.0]
        }
    }
    spec = SpecificationParser(DictSpecificationProvider(spec_dict), plugin_loader).parse()
    config = CommandLineConfiguration(workers=2, runner_type='process', prereq_outdir='prerequisites', outdir=tmpdir, local=True)
    scheduler = LuigiScheduler(config)
    scheduler.run(spawner, spec)

@pytest.mark.skipif('sys.platform != "win32"')
def test_does_not_create_wind_task_when_wind_file_is_set(turbsim_input, fast_input, example_data_folder, tmpdir):
    spawner = FastSimulationSpawner(fast_input, TurbsimSpawner(turbsim_input), tmpdir)
    spawner.wind_file = path.join(example_data_folder, 'fast_input_files', 'wind_files', 'EDC+R+2.0.wnd')
    task = spawner.spawn(path.join(tmpdir, 'a'), {})
    assert len(task.requires()) == 0
    task.run()
    assert task.complete()
