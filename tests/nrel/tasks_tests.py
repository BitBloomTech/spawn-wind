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
import pytest
from os import path
import tempfile
from spawnwind.nrel import FastSimulationTask, WindGenerationTask


def _check_run_fails(task, error_file):
    with pytest.raises(ChildProcessError):
        task.run()
    assert path.isfile(error_file)


@pytest.mark.skipif('sys.platform != "win32"')
def test_runs_fast_with_error():
    temp_dir = tempfile.TemporaryDirectory()
    input_file = path.join(temp_dir.name, 'fast.ipt')
    with open(input_file, 'w') as fp:
        fp.write('some bad FAST input data')
    task = FastSimulationTask('foo', _input_file_path=input_file)
    _check_run_fails(task, path.join(temp_dir.name, 'fast.err'))


@pytest.mark.skipif('sys.platform != "win32"')
def test_run_wind_generation_task_with_error():
    temp_dir = tempfile.TemporaryDirectory()
    input_file = path.join(temp_dir.name, 'turbsim.ipt')
    with open(input_file, 'w') as fp:
        fp.write('some bad wind input data')
    task = WindGenerationTask('wind', _input_file_path=input_file)
    _check_run_fails(task, path.join(temp_dir.name, 'turbsim.err'))
