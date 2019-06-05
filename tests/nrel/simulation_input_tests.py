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

from spawnwind.nrel.nrel_input_line import NrelInputLine
from spawnwind.nrel import TurbsimInput, AerodynInput, NRELSimulationInput, Fast7Input, Fast8Input, TurbsimSpawner
from spawnwind.nrel.fast_input import ElastoDynInput
from spawnwind.nrel.servo_input import ServoDynInput


@pytest.fixture(scope='function')
def turbsim_input(turbsim_input_file):
    return TurbsimInput.from_file(turbsim_input_file)

@pytest.fixture(scope='function')
def aerodyn_input(turbsim_input_file, base_fast_input_folder):
    input_file = path.join(base_fast_input_folder, 'v7', 'NRELOffshrBsline5MW_AeroDyn.ipt')
    return AerodynInput.from_file(input_file, TurbsimSpawner(TurbsimInput.from_file(turbsim_input_file)))

@pytest.fixture(scope='function')
def elastodyn_input(base_fast_input_folder):
    input_file = path.join(base_fast_input_folder, 'v8', 'NRELOffshrBsline5MW_Onshore_ElastoDyn.dat')
    return ElastoDynInput.from_file(input_file)

@pytest.fixture(scope='function')
def servodyn_input(base_fast_input_folder):
    input_file = path.join(base_fast_input_folder, 'v8', 'NRELOffshrBsline5MW_Onshore_ServoDyn.dat')
    return ServoDynInput.from_nrel_input(NRELSimulationInput.from_file(input_file), [1, 2, 3])

@pytest.fixture(scope='function')
def fast7_input(base_fast_input_folder):
    input_file = path.join(base_fast_input_folder, 'v7', 'NRELOffshrBsline5MW_Onshore.fst')
    return Fast7Input.from_file(input_file)

@pytest.fixture(scope='function')
def fast8_input(base_fast_input_folder):
    input_file = path.join(base_fast_input_folder, 'v8', 'NREL5MW.fst')
    return Fast8Input.from_file(input_file)


@pytest.mark.parametrize('input_fixture,key', [
    ('turbsim_input', 'CTStartTime'),
    ('fast7_input', 'NBlGages'),
    ('fast8_input', 'TMax')
])
def test_read_write_round_trip(input_fixture, key, request):
    _input = request.getfixturevalue(input_fixture)
    with tempfile.TemporaryDirectory() as outfile:
        name = path.join(outfile, 'temp.txt')
        _input.to_file(name)
        _input2 = _input.__class__.from_file(name)
    assert _input[key] == _input2[key]


@pytest.mark.parametrize('input_fixture,key,value', [
    ('turbsim_input', 'URef', 11.0),
    ('fast7_input', 'TMax', 300.0),
    ('fast8_input', 'DT', 0.001)
])
def test_writes_edited_Specification(input_fixture, key, value, request):
    _input = request.getfixturevalue(input_fixture)
    _input[key] = value
    with tempfile.TemporaryDirectory() as outfile:
        name = path.join(outfile, 'temp.txt')
        _input.to_file(name)
        _input2 = _input.__class__.from_file(name)
    assert _input2[key] == str(value)


@pytest.mark.parametrize('input_fixture,keys', [
    ('aerodyn_input', ['FoilNm']),
    ('fast7_input', ['BldFile(1)', 'BldFile(3)', 'TwrFile']),
    ('fast8_input', ['EDFile', 'InflowFile', 'ServoFile', 'AeroFile']),
    ('servodyn_input', ['DLL_FileName']),
    ('elastodyn_input', ['BldFile(1)', 'BldFile(3)', 'TwrFile'])
])
def test_paths_are_absolute(input_fixture, keys, request):
    _input = request.getfixturevalue(input_fixture)
    for k in keys:
        f = _input[k]
        #sanitise windows paths
        assert path.isfile(path.sep.join(f.split('\\')))


@pytest.mark.parametrize('input_fixture,key', [
    ('aerodyn_input', 'WindFile'),
    ('fast7_input', 'TwrFile'),
    ('fast8_input', 'EDFile')
])
def test_can_handle_spaces_in_paths(input_fixture, key, request):
    _input = request.getfixturevalue(input_fixture)
    spacey_path = '"C:/this is a spacey/path.ipt"'
    _input[key] = spacey_path
    assert spacey_path.strip('"') == _input[key].strip('"')


def test_can_overwrite_empty_quote(tmpdir):
    lines = [NrelInputLine('""    ThePath   - This is just a comment')]
    input_ = NRELSimulationInput(lines, tmpdir)
    input_['ThePath'] = "a/path"
    assert input_['ThePath'] == 'a/path'
    filepath = path.join(tmpdir, 'input.ipt')
    input_.to_file(filepath)
    with open(filepath, 'r') as fp:
        contents = fp.read()
    assert contents == '"a/path"    ThePath   - This is just a comment'


def test_hash_is_different_for_different_inputs():
    lines = [
        '14            Ref   - This is just a comment',
        '"nrel.txt"    Path   - This is just a comment'
    ]
    input1 = NRELSimulationInput([NrelInputLine(line) for line in lines], '')
    lines[0] = lines[0].replace('14', '15')
    input2 = NRELSimulationInput([NrelInputLine(line) for line in lines], '')
    assert input1.hash() != input2.hash()

