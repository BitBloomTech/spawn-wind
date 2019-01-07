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
import luigi
import numpy as np
from spawn.generate_tasks import generate_tasks_from_spec
from spawn.tasks.simulation import SimulationTask
from spawn.parsers import *
from spawn.parsers.value_proxy import ValueProxyParser

from spawnwind.nrel import WindGenerationTask, FastSimulationSpawner

def test_can_create_1d_set_of_aeroelastic_tasks(tmpdir, spawner):
    run_spec = {'wind_speed': list(np.arange(4.0, 15.0, 2.0))}
    root_node = SpecificationNodeParser(ValueProxyParser({})).parse(run_spec)
    tasks = generate_tasks_from_spec(spawner, root_node, tmpdir.strpath)
    assert len(tasks) == 6
    for t in tasks:
        assert isinstance(t, SimulationTask)
        assert len(t.requires()) == 1
        assert isinstance(t.requires()[0], WindGenerationTask)
        assert path.isdir(path.split(t.run_name_with_path)[0])
        assert tmpdir.strpath in t.run_name_with_path
        assert 'wind_speed' in t.metadata


def test_can_create_runs_from_tree_spec(tmpdir, spawner, plugin_loader, example_data_folder):
    input_path = path.join(example_data_folder, 'iec_fatigue_spec.json')
    spec_model = SpecificationParser(SpecificationFileReader(input_path), plugin_loader).parse()
    runs = generate_tasks_from_spec(spawner, spec_model.root_node, tmpdir.strpath)
    assert len(runs) == 12*3 + 12*2 + 12*3
    seeds = []
    for t in runs:
        assert isinstance(t, SimulationTask)
        assert len(t.requires()) == 1
        assert isinstance(t.requires()[0], WindGenerationTask)
        assert path.isdir(path.split(t.run_name_with_path)[0])
        assert tmpdir.strpath in t.run_name_with_path
        assert 'wind_speed' in t.metadata
        assert 'turbulence_seed' in t.metadata
        assert 'wind_direction' in t.metadata or 'rotor_azimuth' in t.metadata
        seeds.append(t.metadata['turbulence_seed'])
    assert len(seeds) == len(set(seeds))  # testing uniqueness

def test_can_run_one_turbsim_and_fast_run(tmpdir, example_data_folder, spawner):
    spec = {
        "base_wind_input": path.join(example_data_folder, 'fast_input_files', 'TurbSim.inp'),
        "wind_executable": path.join(example_data_folder, 'TurbSim.exe'),
        "base_time_domain_input": path.join(example_data_folder, 'fast_input_files', 'NRELOffshrBsline5MW_Onshore.fst'),
        "time_domain_executable": path.join(example_data_folder, 'FASTv7.0.2.exe'),
        "output_base_dir": tmpdir.strpath,
        "runs": [{'wind_speed': 8.0, 'output_start_time': 0.0, 'simulation_time': 1.0}]
    }
    run_spec = {
        'wind_speed': 8.0, 'output_start_time': 0.0, 'simulation_time': 1.0
    }
    root_node = SpecificationNodeParser(ValueProxyParser({})).parse(run_spec)
    tasks = generate_tasks_from_spec(spawner, root_node, tmpdir.strpath)
    luigi.build(tasks, local_scheduler=True, log_level='WARNING')
    assert tasks[0].output().exists()
