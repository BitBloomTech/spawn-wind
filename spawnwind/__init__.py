# spawnwind
# Copyright (C) 2018-2019, Simmovation Ltd.
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
"""Wind plugin for :mod:`spawn`
"""
from spawn.plugins import PluginLoader
from spawn.config import DefaultConfiguration

import spawnwind.nrel.plugin as nrel_plugin

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

PluginLoader.pre_load_plugin('nrel', nrel_plugin)
DefaultConfiguration.set_default('type', 'nrel')
