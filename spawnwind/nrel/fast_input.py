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
"""
Handlers of Main FAST input file
"""
from .wind_input import AerodynInput, InflowWindInput
from .aero_input import AerodynPre15AeroInput, Aerodyn15AeroInput
from .simulation_input import NRELSimulationInput
from .servo_input import Fast7ServoInput, ServoDynInput


class ElastoDynInput(NRELSimulationInput):
    """
    Input handler for ElastoDyn (v8.12 and later)
    """
    key = 'EDFile'

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key not in ['OutFile', 'DLL_FileName']
        return self._get_indices_if(is_file_path)


class FastInput(NRELSimulationInput):
    """
    Base class manager for main FAST input file
    """
    def get_wind_input(self, wind_gen_spawner):
        """
        :param wind_gen_spawner: Spawner of wind generation tasks
        :return: :class:`WindInput` instance for managing the contents of the input file for wind inflow
        """
        raise NotImplementedError()

    def get_aero_input(self, wind_input):
        """
        :param wind_input: :class:`WindInput` instance, which will be used also for aerodynamic input if they are in the
         same file such as in FAST 7
        :return: :class:`AeroInput` instance for managing the aerodynamic setting inputs
        """
        raise NotImplementedError()

    def get_servodyn_input(self, blade_range):
        """
        :param blade_range: iterable containing the numbers of the blades (e.g. [1, 2, 3])
        :return: A :class:`FastServoInput` instance for managing control and manoeuvre inputs
        """
        raise NotImplementedError()

    def get_elastodyn_input(self):
        """
        :return: An instance responsible for handling structural inputs
        """
        raise NotImplementedError()


class Fast7Input(FastInput):
    """
    Manager for main FAST input file v7
    """
    def _lines_with_paths(self):
        def is_file_path(key):
            return key in ['TwrFile', 'ADFile', 'ADAMSFile'] or 'BldFile' in key
        return self._get_indices_if(is_file_path)

    def get_wind_input(self, wind_gen_spawner):
        return AerodynInput.from_file(self['ADFile'], wind_gen_spawner)

    def get_aero_input(self, wind_input):
        return AerodynPre15AeroInput.from_aerodyn_input(wind_input)

    def get_servodyn_input(self, blade_range):
        return Fast7ServoInput.from_nrel_input(self, blade_range)

    def get_elastodyn_input(self):
        return self


class Fast8Input(FastInput):
    """
    Manager for main FAST input file v8
    """
    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFileFmt'
        return self._get_indices_if(is_file_path)

    def get_wind_input(self, wind_gen_spawner):
        return InflowWindInput.from_file(self['InflowFile'], wind_gen_spawner)

    def get_aero_input(self, _wind_input):
        aerodyn_type = int(self['CompAero'])
        if aerodyn_type == 1:
            aero_input = AerodynPre15AeroInput.from_file(self['AeroFile'])
            aero_input.key = 'AeroFile'  # so that this file is written by parent spawner
            return aero_input
        if aerodyn_type == 2:
            return Aerodyn15AeroInput.from_file(self[Aerodyn15AeroInput.key])
        return None

    def get_servodyn_input(self, blade_range):
        return ServoDynInput.from_nrel_input(NRELSimulationInput.from_file(self[ServoDynInput.key]), blade_range)

    def get_elastodyn_input(self):
        return ElastoDynInput.from_file(self[ElastoDynInput.key])
