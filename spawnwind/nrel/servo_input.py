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
Handlers of input files relating to control and manoeuvre information
"""
from .simulation_input import NRELSimulationInput


class FastServoInput(NRELSimulationInput):
    """
    Base class for managing inputs relating to control and manoeuvres
    """

    def __init__(self, blade_range, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._blade_range = blade_range

    @classmethod
    def from_nrel_input(cls, nrel_input, blade_range):
        """
        Create from :class:`NRELSimulationInput` instance
        :param nrel_input: :class:`NRELSimulationInput` instance
        :param blade_range:
        :return: :class:`FastServoInput` instance
        """
        if not isinstance(nrel_input, NRELSimulationInput):
            raise TypeError("'nrel_input' not of type 'NRELSimulationInput'")
        # pylint: disable=protected-access
        return cls(blade_range, nrel_input._input_lines, nrel_input._root_folder)

    # Pitch
    def get_blade_pitch_manoeuvre_time(self, blade_number):
        """
        :param blade_number: Integer blade number
        :return: Time in seconds at which blade starts pitching in pitch manoeuvre
        """
        return float(self.get_on_blade('TPitManS', blade_number))

    def set_blade_pitch_manoeuvre_time(self, blade_number, time):
        """
        :param blade_number: Integer blade number
        :param time: Time in seconds at which blade starts pitching in pitch manoeuvre
        """
        self.set_on_blade('TPitManS', blade_number, time)

    @property
    def final_pitch(self):
        """
        This function is not implemented because it is not possible to determine a single scalar value
        :return: Final pitch angle of manoeuvre in degrees
        """
        # pylint: disable=abstract-method
        raise NotImplementedError('Incapable of determining final pitch angle for all blades at once')

    @final_pitch.setter
    def final_pitch(self, angle):
        for bld_num in self._blade_range:
            self.set_blade_final_pitch(bld_num, angle)

    def get_blade_final_pitch(self, blade_number):
        """
        :param blade_number: Integer blade number
        :return: Final pitch angle of manoeuvre in degrees
        """
        return float(self.get_on_blade('BlPitchF', blade_number))

    def set_blade_final_pitch(self, blade_number, angle):
        """
        :param blade_number: Integer blade number
        :param angle: Final pitch angle of manoeuvre in degrees
        """
        self.set_on_blade('BlPitchF', blade_number, angle)

    @property
    def pitch_control_start_time(self):
        """
        :return: Time in seconds at which pitch control is activated
        """
        return float(self['TPCOn'])

    @pitch_control_start_time.setter
    def pitch_control_start_time(self, time):
        self['TPCOn'] = time

    @property
    def pitch_manoeuvre_rate(self):
        """
        :return: Rate in degrees per second at which blade pitches during pitch manoeuvres
        """
        raise NotImplementedError()

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        raise NotImplementedError()

    def get_blade_pitch_manoeuvre_end_time(self, blade_number):
        """
        :param blade_number: Integer blade number
        :return: Time in seconds at which blade stops pitching in pitch manoeuvre
        """
        return float(self.get_on_blade('TPitManE', blade_number))

    def set_blade_pitch_manoeuvre_end_time(self, blade_number, time):
        """
        :param blade_number: Integer blade number
        :param time: Time in seconds at which blade stops pitching in pitch manoeuvre
        """
        self.set_on_blade('TPitManE', blade_number, time)

    def reconcile_pitch_manoeuvre(self, blade_number, initial_pitch):
        """
        Reconcile pitch manoeuvres by matching manoeuvre start and end times, start and end pitch angles and manoeuvre
        rate
        :param blade_number: Blade number on which to reconcile
        :param initial_pitch: Initial pitch angle in degrees (external parameter)
        """

    # Yaw
    @property
    def yaw_manoeuvre_time(self):
        """
        :return: Time in seconds at which yaw manoeuvre starts
        """
        return float(self['TYawManS'])

    @yaw_manoeuvre_time.setter
    def yaw_manoeuvre_time(self, time):
        self['TYawManS'] = time
        self['YCMode'] = 0

    @property
    def final_yaw(self):
        """
        :return: Final yaw angle of manoeuvre in degrees
        """
        return float(self['NacYawF'])

    @final_yaw.setter
    def final_yaw(self, angle):
        self['NacYawF'] = angle

    @property
    def yaw_manoeuvre_rate(self):
        """
        :return: Rate at which turbine yaws in degrees per second during yaw manoeuvre
        """
        raise NotImplementedError()

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        raise NotImplementedError()

    def reconcile_yaw_manoeuvre(self, initial_yaw):
        """
        Reconcile yaw manoeuvres by matching manoeuvre start and end times, start and end yaw angles and manoeuvre rate
        :param initial_yaw: Initial yaw angle in degrees (external parameter)
        """


# pylint: disable=abstract-method
class Fast7ServoInput(FastServoInput):
    """
    Handles control and manoeuvres via the main FAST input file (FAST v7)
    """
    def __init__(self, *args):
        super().__init__(*args)
        self._pitch_manoeuvre_rate = None
        self._yaw_manoeuvre_rate = None

    @property
    def pitch_manoeuvre_rate(self):
        return self._pitch_manoeuvre_rate

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        self._pitch_manoeuvre_rate = float(pitch_rate)

    def reconcile_pitch_manoeuvre(self, blade_number, initial_pitch):
        if self._pitch_manoeuvre_rate:  # is not None and != 0.0
            delta_pitch = (self.get_blade_final_pitch(blade_number) - initial_pitch) / self._pitch_manoeuvre_rate
            self.set_on_blade('TPitManE', blade_number,
                              float(self.get_on_blade('TPitManS', blade_number)) + delta_pitch)
        else:
            self.set_blade_pitch_manoeuvre_end_time(blade_number, self.get_blade_pitch_manoeuvre_time(blade_number))

    @property
    def yaw_manoeuvre_rate(self):
        return self._yaw_manoeuvre_rate

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        self._yaw_manoeuvre_rate = float(rate)

    def reconcile_yaw_manoeuvre(self, initial_yaw):
        if self._yaw_manoeuvre_rate:  # is not None and != 0.0
            self['TYawManE'] = self.yaw_manoeuvre_time + \
                (self.final_yaw - initial_yaw) / self._yaw_manoeuvre_rate
        else:
            self['TYawManE'] = self['TYawManS']


# pylint: disable=abstract-method
class ServoDynInput(FastServoInput):
    """
    Handles control and manoeuvres via the ServoDyn input file (FAST v8)
    """
    key = 'ServoFile'

    @property
    def pitch_manoeuvre_rate(self):
        return float(self.get_on_blade('PitManRat', 1))

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        if pitch_rate != 0.0:
            for bld_num in self._blade_range:
                self.set_on_blade('PitManRat', bld_num, pitch_rate)
        else:
            # v8 does not allow zero pitch rate so set manoeuvre time to large instead
            for bld_num in self._blade_range:
                self.set_blade_pitch_manoeuvre_time(bld_num, 9999.9)

    @property
    def yaw_manoeuvre_rate(self):
        return float(self['YawManRat'])

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        self['YawManRat'] = rate

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFile'
        return self._get_indices_if(is_file_path)
