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
from spawn.config import DefaultConfiguration, CompositeConfiguration, CommandLineConfiguration

from spawnwind.nrel import TurbsimInput, Fast7Input, Fast8Input, TurbsimSpawner, FastSimulationSpawner

__home_dir = path.dirname(path.realpath(__file__))
_example_data_folder = path.join(__home_dir, pardir, 'example_data')

@pytest.fixture(scope='session')
def exe_paths():
    return {
        'turbsim': path.join(_example_data_folder, 'TurbSim.exe'),
        'fast_v7': path.join(_example_data_folder, 'FASTv7.0.2.exe'),
        'fast_v8': path.join(_example_data_folder, 'FASTv8.16_Win32.exe')
    }

@pytest.fixture(scope='session', autouse=True)
def configure_luigi(exe_paths):
    luigi.configuration.get_config().set('WindGenerationTask', '_runner_type', 'process')
    luigi.configuration.get_config().set('WindGenerationTask', '_exe_path', exe_paths['turbsim'])
    luigi.configuration.get_config().set('FastSimulationTask', '_runner_type', 'process')
    luigi.configuration.get_config().set('FastSimulationTask', '_exe_path', exe_paths['fast_v8'])

@pytest.fixture(params=['v7', 'v8'], scope='module')
def fast_version(request, exe_paths):
    if request.param == 'v8':
        luigi.configuration.get_config().set('FastSimulationTask', '_exe_path', exe_paths['fast_v8'])
    elif request.param == 'v7':
        luigi.configuration.get_config().set('FastSimulationTask', '_exe_path', exe_paths['fast_v7'])
    return request.param

@pytest.fixture(scope='module')
def turbsim_input_file():
    return path.join(_example_data_folder, 'fast_input_files', 'TurbSim.inp')

@pytest.fixture(scope='module')
def inflowwind_input_file():
    return path.join(_example_data_folder, 'fast_input_files', 'v8', 'InflowWind.inp')

@pytest.fixture(scope='module')
def fast_input_file(fast_version):
    if fast_version == 'v7':
        return path.join(_example_data_folder, 'fast_input_files', 'NRELOffshrBsline5MW_Onshore.fst')
    elif fast_version == 'v8':
        return path.join(_example_data_folder, 'fast_input_files', 'v8', 'NREL5MW.fst')

@pytest.fixture(scope='function')
def fast_input(fast_version, fast_input_file):
    if fast_version == 'v7':
        return Fast7Input.from_file(fast_input_file)
    elif fast_version == 'v8':
        return Fast8Input.from_file(fast_input_file)

@pytest.fixture(scope='module')
def example_data_folder():
    return _example_data_folder

@pytest.fixture
def examples_folder(example_data_folder):
    return path.join(example_data_folder, 'fast_input_files')

@pytest.fixture
def wind_gen_spawner(turbsim_input_file):
    return TurbsimSpawner(TurbsimInput.from_file(turbsim_input_file))

@pytest.fixture
def spawner(wind_gen_spawner, fast_v7_input_file, tmpdir):
    return FastSimulationSpawner(Fast7Input.from_file(fast_v7_input_file), wind_gen_spawner, tmpdir)

@pytest.fixture
def plugin_loader(tmpdir, exe_paths):
    default_config = DefaultConfiguration()
    command_line_configuration = CommandLineConfiguration(
        turbsim_exe=exe_paths['turbsim'], fast_exe=exe_paths['fast_v7'],
        turbsim_base_file=path.join(_example_data_folder, 'fast_input_files', 'TurbSim.inp'),
        fast_base_file=path.join(_example_data_folder, 'fast_input_files', 'NRELOffshrBsline5MW_Onshore.fst'),
        turbsim_working_dir=_example_data_folder,
        fast_working_dir=_example_data_folder,
        outdir=str(tmpdir)
    )
    return PluginLoader(CompositeConfiguration(command_line_configuration, default_config))
