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
Handlers of input files relating to aerodynamic settings. Not that options relating to wind environment are in
 `wind_input`.
"""
from .simulation_input import NRELSimulationInput
from .wind_input import AerodynInput


class AeroInput(NRELSimulationInput):
    """
    Base class for managing inputs relating to aerodynamic settings
    """
    @property
    def wake_model_on(self):
        """
        Whether wake/induction model is enabled
        """
        raise NotImplementedError()

    @wake_model_on.setter
    def wake_model_on(self, on):
        raise NotImplementedError()

    @property
    def dynamic_stall_on(self):
        """
        Whether dynamic stall model is enabled (FAST only has Beddoes-Leishman model)
        """
        raise NotImplementedError()

    @dynamic_stall_on.setter
    def dynamic_stall_on(self, on):
        raise NotImplementedError()

    def _lines_with_paths(self):
        def is_blade_file(key):
            return 'File' in key
        return self._airfoil_lines() + self._get_indices_if(is_blade_file)

    def _airfoil_lines(self):
        raise NotImplementedError()


class AerodynPre15AeroInput(AeroInput):
    """
    Manages aerodynamic setting inputs in Aerodyn file formats for Aerodyn version 14 and earlier
    """
    @classmethod
    def from_aerodyn_input(cls, aerodyn_input):
        """
        Create from an Aerodyn input so that the two objects write to the same input
        :param aerodyn_input: :class:`AerodynInput` instance
        :return: :class:`Fast7AeroInput` instance
        """
        if not isinstance(aerodyn_input, AerodynInput):
            raise TypeError("'aerodyn_input' not of type 'AerodynInput'")
        # pylint: disable=protected-access
        return cls(aerodyn_input._input_lines, aerodyn_input._root_folder)

    @property
    def wake_model_on(self):
        return self['IndModel'] != 'NONE'

    @wake_model_on.setter
    def wake_model_on(self, on):
        self['IndModel'] = 'SWIRL' if on else 'NONE'

    @property
    def dynamic_stall_on(self):
        return self['StallMod'] != 'STEADY'

    @dynamic_stall_on.setter
    def dynamic_stall_on(self, on):
        self['StallMod'] = 'BEDDOES' if on else 'STEADY'

    def _airfoil_lines(self):
        i = self._get_index('NumFoil')
        number_of_airfolis = int(self._input_lines[i].value)
        return list(range(i+1, i+number_of_airfolis+1))


class Aerodyn15AeroInput(AeroInput):
    """
    Manages aerodynamic setting inputs in Aerodyn v15 and later
    """
    key = 'AeroFile'

    @property
    def wake_model_on(self):
        return int(self['WakeMod']) > 0

    @wake_model_on.setter
    def wake_model_on(self, on):
        self['WakeMod'] = 1 if on else 0

    @property
    def dynamic_stall_on(self):
        return int(self['AFAeroMod']) > 1

    @dynamic_stall_on.setter
    def dynamic_stall_on(self, on):
        self['AFAeroMod'] = 2 if on else 1

    def _airfoil_lines(self):
        i = self._get_index('NumAFfiles')
        number_of_airfolis = int(self._input_lines[i].value)
        return list(range(i+1, i+number_of_airfolis+1))
