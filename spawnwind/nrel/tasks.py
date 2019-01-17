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
"""NREL Tasks
"""
from os import path

import luigi

from spawn.tasks import SimulationTask

class WindGenerationTask(SimulationTask):
    """Implementation of :class:`SimulationTask` for TurbSim
    """
    def output(self):
        """The output of this task

        :returns: Target to the .wnd path
        :rtype: :class:`luigi.LocalTarget`
        """
        return luigi.LocalTarget(self.wind_file_path)

    @property
    def wind_file_path(self):
        """The path to the wind file
        """
        return super().run_name_with_path + '.wnd'

class FastSimulationTask(SimulationTask):
    """Implementation of :class:`SimulationTask` for FAST
    """
    def output(self):
        """The output of this task

        :returns: Target to the .outb path
        :rtype: :class:`luigi.LocalTarget`
        """
        run_name_with_path = path.splitext(super().run_name_with_path)[0]
        output = run_name_with_path + '.outb'
        return luigi.LocalTarget(output)
