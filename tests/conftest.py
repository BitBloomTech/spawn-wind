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
from os import path, pardir

import pytest

import luigi.configuration

from spawn.plugins import PluginLoader
from spawn.config import DefaultConfiguration

from spawnwind.nrel import TurbsimInput, FastInput, TurbsimSpawner, FastSimulationSpawner

__home_dir = path.dirname(path.realpath(__file__))
_example_data_folder = path.join(__home_dir, pardir, 'example_data')

EXE_PATHS = {
    'turbsim': path.join(_example_data_folder, 'TurbSim.exe'),
    'fast': path.join(_example_data_folder, 'FASTv7.0.2.exe')
}

@pytest.fixture(scope='module')
def turbsim_exe():
    return path.join(_example_data_folder, 'TurbSim.exe')

@pytest.fixture(scope='module')
def fast_exe():
    return path.join(_example_data_folder, 'FASTv7.0.2.exe')

@pytest.fixture(scope='module')
def turbsim_input_file():
    return path.join(_example_data_folder, 'fast_input_files', 'TurbSim.inp')

@pytest.fixture(scope='module')
def fast_input_file():
    return path.join(_example_data_folder, 'fast_input_files', 'NRELOffshrBsline5MW_Onshore.fst')

@pytest.fixture(scope='module')
def example_data_folder():
    return _example_data_folder

@pytest.fixture
def examples_folder(example_data_folder):
    return path.join(example_data_folder, 'fast_input_files')

@pytest.fixture
def turbsim_exe(example_data_folder):
    return path.join(example_data_folder, 'TurbSim.exe')

@pytest.fixture
def fast_exe(example_data_folder):
    return path.join(example_data_folder, 'FASTv7.0.2.exe')

@pytest.fixture(scope='session', autouse=True)
def configure_luigi():
    luigi.configuration.get_config().set('WindGenerationTask', '_runner_type', 'process')
    luigi.configuration.get_config().set('WindGenerationTask', '_exe_path', EXE_PATHS['turbsim'])
    luigi.configuration.get_config().set('FastSimulationTask', '_runner_type', 'process')
    luigi.configuration.get_config().set('FastSimulationTask', '_exe_path', EXE_PATHS['fast'])

@pytest.fixture
def spawner(example_data_folder, tmpdir):
    wind_spawner = TurbsimSpawner(TurbsimInput.from_file(path.join(example_data_folder, 'fast_input_files',
                                                                   'TurbSim.inp')))
    return FastSimulationSpawner(FastInput.from_file(path.join(example_data_folder, 'fast_input_files',
                                                               'NRELOffshrBsline5MW_Onshore.fst')),
                                 wind_spawner, tmpdir)

@pytest.fixture
def plugin_loader():
    return PluginLoader(DefaultConfiguration())
