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
Handlers of input files relating to wind inflow
"""
from os import path
from .nrel_input_line import NrelInputLine
from .simulation_input import NRELSimulationInput


class WindInput(NRELSimulationInput):
    """
    Base class for NREL input file determining the wind conditions for a FAST simulation. In FAST v7, this is an Aerodyn
     input file and in v8 it is the InflowWind input file
    """

    def __init__(self, lines, root_folder, wind_gen_spawner):
        """
        :param lines: Lines, each with a key and value, making up the wind input
        :type lines: list of :class:`NrelInputLine`
        :param root_folder: The root folder containing the input file
        :param wind_gen_spawner: Spawner for wind generation tasks into which properties relating to wind generation are
         set
        """
        super().__init__(lines, root_folder)
        self._wind_gen_spawner = wind_gen_spawner
        self._wind_task_cache = {}
        self._wind_is_explicit = False

    @classmethod
    # pylint: disable=arguments-differ
    def from_file(cls, file_path, wind_gen_spawner):
        with open(file_path, 'r') as fp:
            input_lines = fp.readlines()
        root_folder = path.abspath(path.split(file_path)[0])
        return cls([NrelInputLine(line) for line in input_lines], root_folder, wind_gen_spawner)

    def get_wind_gen_tasks(self, prereq_dir, metadata):
        """
        Create wind generation tasks to create new wind find if necessary
        :param prereq_dir: Output directory for prerequisite simulations
        :param metadata: Metadata for wind generation task
        :return: list of wind generation tasks (size 0 or 1)
        """
        raise NotImplementedError()

    @property
    def wind_gen_spawner(self):
        """
        :return: underlying spawner for wind generation tasks
        """
        return self._wind_gen_spawner

    @wind_gen_spawner.setter
    def wind_gen_spawner(self, spawner):
        """
        :param spawner: underlying spawner for wind generation tasks
        """
        self._wind_gen_spawner = spawner

    @property
    def wind_type(self):
        """
        :return: Type of wind as a lowercase string (.e.g. 'bladed', 'turbsim', 'steady')
        """
        raise NotImplementedError()

    @wind_type.setter
    def wind_type(self, type_):
        """
        :param type_: Lowercase string representing wind type (.e.g 'bladed' or 'turbsim')
        """
        raise NotImplementedError()

    @property
    def wind_speed(self):
        """
        :return: Reference wind speed in m/s
        """
        return self._wind_gen_spawner.wind_speed

    @wind_speed.setter
    def wind_speed(self, speed):
        """
        :param speed: Reference wind speed in m/s
        """
        self._wind_gen_spawner.wind_speed = speed

    @property
    def turbulence_intensity(self):
        """
        :return: Turbulence intensity as a percentage
        """
        return self._wind_gen_spawner.turbulence_intensity

    @turbulence_intensity.setter
    def turbulence_intensity(self, turbulence_intensity):
        """
        :param turbulence_intensity: Turbulence intensity as a percentage
        """
        self._wind_gen_spawner.turbulence_intensity = turbulence_intensity

    @property
    def turbulence_seed(self):
        """
        :return: Integer turbulence seed for wind file generation
        """
        return self._wind_gen_spawner.turbulence_seed

    @turbulence_seed.setter
    def turbulence_seed(self, seed):
        self._wind_gen_spawner.turbulence_seed = seed

    @property
    def wind_shear(self):
        """
        :return: Wind shear exponent
        """
        return self._wind_gen_spawner.wind_shear

    @wind_shear.setter
    def wind_shear(self, exponent):
        self._wind_gen_spawner.wind_shear = exponent

    @property
    def upflow(self):
        """
        :return: Mean wind flow inclination in degrees upwards from the horizontal
        """
        return self._wind_gen_spawner.upflow

    @upflow.setter
    def upflow(self, angle):
        self._wind_gen_spawner.upflow = angle

    @property
    def wind_file(self):
        """
        :return: Path of wind file if set
        """
        return self['WindFile']

    @wind_file.setter
    def wind_file(self, file):
        self._set_wind_file(file)
        self._wind_is_explicit = True

    def _set_wind_file(self, file):
        """
        :param file: path of wind file
        :return: Set wind file path in input
        """
        raise NotImplementedError()

    def _spawn_wind_gen_task(self, prereq_dir, metadata):
        """
        Get wind task from hash if equivalent exists, otherwise spawn new wind generation task
        :param prereq_dir: Output directory for prerequisite simulations
        :param metadata: Metadata for siumulation
        :return: WindGenerationTask
        """
        wind_hash = self._wind_gen_spawner.input_hash()
        if wind_hash in self._wind_task_cache:
            wind_task = self._wind_task_cache[wind_hash]
        else:
            outdir = path.join(prereq_dir, wind_hash)
            wind_task = self._wind_gen_spawner.spawn(outdir, metadata)
            self._wind_task_cache[wind_hash] = wind_task
        return wind_task


class AerodynInput(WindInput):
    """Handles contents of Aerodyn (FAST aerodynamics) input file, which defines wind input for versions < 8.12"""
    key = 'ADFile'

    def get_wind_gen_tasks(self, prereq_dir, metadata):
        # Generate new wind file if needed
        if self._wind_is_explicit:
            return []

        wind_task = self._spawn_wind_gen_task(prereq_dir, metadata)
        self._set_wind_file(wind_task.wind_file_path)
        return [wind_task]

    @property
    def wind_type(self):
        return self._wind_gen_spawner.wind_type

    @wind_type.setter
    def wind_type(self, type_):
        if type_ in ['bladed', 'turbsim']:
            self._wind_gen_spawner.wind_type = type_

    def _set_wind_file(self, file):
        self['WindFile'] = file

    def _lines_with_paths(self):
        num_foils = int(self['NumFoil'])
        index = self._get_index('FoilNm')
        return range(index, index + num_foils)


class InflowWindInput(WindInput):
    """Handles contents of InflowWind input file which handles wind input of FAST in versions >= 8.12"""
    key = 'InflowFile'
    _wind_type_names = {
        1: 'steady',
        2: 'uniform',
        3: 'turbsim',
        4: 'bladed',
        5: 'hawc',
        6: 'dll'
    }
    _wind_type_numbers = {
        'steady': 1,
        'uniform': 2,
        'turbsim': 3,
        'bladed': 4,
        'hawc': 5,
        'dll': 6
    }

    def get_wind_gen_tasks(self, prereq_dir, metadata):
        """
        Create wind generation tasks to create new wind find if necessary
        :param prereq_dir: Output directory for prerequisite simulations
        :param metadata: Metadata for wind generation task
        :return: list of wind generation tasks (size 0 or 1)
        """
        # Generate new wind file if needed
        if self.wind_type == 'steady' or self.wind_type == 'uniform' or self._wind_is_explicit:
            return []

        wind_task = self._spawn_wind_gen_task(prereq_dir, metadata)
        self._set_wind_file(wind_task.wind_file_path)
        return [wind_task]

    @property
    def wind_type(self):
        type_num = int(self['WindType'])
        return self._wind_type_names[type_num]

    @wind_type.setter
    def wind_type(self, type_name):
        if type_name not in self._wind_type_numbers:
            raise ValueError('Invalid wind type')
        self['WindType'] = self._wind_type_numbers[type_name]
        if type_name in ['bladed', 'turbsim']:
            self._wind_gen_spawner.wind_type = type_name

    @property
    def wind_speed(self):
        if self.wind_type == 'steady':
            return float(self['HWindSpeed'])
        else:
            return float(self._wind_gen_spawner.wind_speed)

    @wind_speed.setter
    def wind_speed(self, speed):
        if self.wind_type == 'steady':
            self['HWindSpeed'] = speed
        else:
            self._wind_gen_spawner.wind_speed = speed

    @property
    def wind_file(self):
        return self._get_wind_file_line().value

    @wind_file.setter
    def wind_file(self, file):
        self._get_wind_file_line().value = file

    def _lines_with_paths(self):
        def _is_filepath_key(key):
            return 'filename' in key.lower()
        return self._get_indices_if(_is_filepath_key)

    def _get_wind_file_line(self):
        type_ = int(self['WindType'])
        filename_key_with_type = 'FilenameT{}'.format(type_)
        if type_ == 2:
            try:
                return self._get_line(filename_key_with_type)
            except KeyError:
                return self._get_line('Filename')
        elif type_ == 3:
            try:
                return self._get_line(filename_key_with_type)
            except KeyError:
                return self._get_line('Filename', 2)
        elif type_ == 4:
            try:
                return self._get_line(filename_key_with_type)
            except KeyError:
                return self._get_line('FilenameRoot')
        else:
            raise KeyError("Cannot find wind file in InflowWind, type_={}. "\
                           "Set 'wind_type' parameter to an appropriate value".format(type_))

    def _set_wind_file(self, file):
        line = self._get_wind_file_line()
        line.value = path.splitext(file)[0] if (line.key == 'FilenameRoot' or line.key == 'FilenameT4') else file
