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
from spawnwind.nrel import TurbsimInput, AerodynInput, FastInput


@pytest.mark.parametrize('cls,file,key', [
    (TurbsimInput, 'TurbSim.inp', 'CTStartTime'),
    (AerodynInput, 'NRELOffshrBsline5MW_AeroDyn.ipt', 'BldNodes'),
    (FastInput, 'NRELOffshrBsline5MW_Onshore.fst', 'NBlGages')
])
def test_read_write_round_trip(examples_folder, cls, file, key):
    _input = cls.from_file(path.join(examples_folder, file))
    with tempfile.TemporaryDirectory() as outfile:
        name = path.join(outfile, 'temp.txt')
        _input.to_file(name)
        _input2 = cls.from_file(name)
    assert _input[key] == _input2[key]


@pytest.mark.parametrize('cls,file,key,value', [
    (TurbsimInput, 'TurbSim.inp', 'URef', 11.0),
    (AerodynInput, 'NRELOffshrBsline5MW_AeroDyn.ipt', 'WindFile', 'Other.wnd'),
    (FastInput, 'NRELOffshrBsline5MW_Onshore.fst', 'TMax', 300.0)
])
def test_writes_edited_Specification(examples_folder, cls, file, key, value):
    _input = cls.from_file(path.join(examples_folder, file))
    _input[key] = value
    with tempfile.TemporaryDirectory() as outfile:
        name = path.join(outfile, 'temp.txt')
        _input.to_file(name)
        _input2 = cls.from_file(name)
    assert _input2[key] == str(value)


@pytest.mark.parametrize('cls,file,keys', [
    (AerodynInput, 'NRELOffshrBsline5MW_AeroDyn.ipt', ['FoilNm']),
    (FastInput, 'NRELOffshrBsline5MW_Onshore.fst', ['BldFile(1)', 'BldFile(3)', 'TwrFile'])
])
def test_paths_are_absolute(examples_folder, cls, file, keys):
    _input = cls.from_file(path.join(examples_folder, file))
    for k in keys:
        f = _input[k]
        assert path.isfile(f)


@pytest.mark.parametrize('cls,file,key', [
    (AerodynInput, 'NRELOffshrBsline5MW_AeroDyn.ipt', 'WindFile'),
    (FastInput, 'NRELOffshrBsline5MW_Onshore.fst', 'TwrFile')
])
def test_can_handle_spaces_in_paths(examples_folder, cls, file, key):
    _input = cls.from_file(path.join(examples_folder, file))
    spacey_path = '"C:/this is a spacey/path.ipt"'
    _input[key] = spacey_path
    assert spacey_path.strip('"') == _input[key].strip('"')
