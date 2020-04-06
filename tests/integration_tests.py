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
import json

import spawn
from spawn.config import DefaultConfiguration


def test_successfully_inspects_iec_spec(example_data_folder):
    input_path = path.join(example_data_folder, 'iec_spec.json')
    with open(input_path) as fp:
        spec = json.load(fp)

    stats = spawn.stats(spec, {'format': 'json'})
    assert stats['leaf_count'] == 1591
    inspection = spawn.inspect(spec, {'format': 'json'})
    assert isinstance(inspection, dict)
    assert 'spec' in inspection


def test_plugin_loader_has_nrel_plugin_loaded(plugin_loader):
    assert plugin_loader.create_spawner('nrel')


def test_default_type_is_nrel():
    assert DefaultConfiguration().get('spawn', 'type') == 'nrel'
