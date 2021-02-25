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
"""Contains definitions for NREL :class:`SimulationInput`
"""
from os import path
from spawn.simulation_inputs import SimulationInput
from spawn.util.hash import string_hash
from .nrel_input_line import NrelInputLine


def _absolutise_path(line, root_dir, local_path):
    local_path = local_path.strip('"')
    return line.replace(local_path, str(path.join(root_dir, local_path)))


class NRELSimulationInput(SimulationInput):
    """
    Handles contents of input files for NREL's aeroelastic modules such as FAST, AeroDyn and TurbSim.
    These tend to be of a whitespace separated {value|key} format with newlines separating key:value pairs
    """
    def __init__(self, input_lines, root_folder, key_separator='.'):
        """Initialises :class:`NRELSimulationInput`

        :param input_lines: The lines of the input file
        :type input_lines: list
        :param root_folder: The root folder containing the input file
        :type root_folder: path-like
        :param key_separator: the character used to separate keys in a chain for nested access e.g. 'EDFile.NacYaw'
        :type key_separator: str
        """
        self._input_lines = input_lines
        self._root_folder = root_folder
        self._key_separator = key_separator
        self._nested_inputs = {}
        self._absolutise_paths(root_folder, self._lines_with_paths())

    # pylint: disable=arguments-differ
    @classmethod
    def from_file(cls, file_path, **kwargs):
        """Creates a :class:`NRELSimulationInput` by loading a file

        :param file_path: The file path to load
        :type file_path: path-like

        :returns: The simulation input object
        :rtype: An instance of :class:`NRELSimulationInput`
        """
        with open(file_path, 'r') as fp:
            input_lines = fp.readlines()
        root_folder = path.abspath(path.split(file_path)[0])
        return cls([NrelInputLine(line) for line in input_lines], root_folder, **kwargs)

    def to_file(self, file_path):
        """Writes the contents of the input file to disk

        :param file_path: The path of the file to write
        :type file_path: path-like
        """
        with open(file_path, 'w') as fp:
            for line in self._input_lines:
                fp.write(str(line))
        return file_path

    def hash(self):
        """Returns a hash of the contents of the file

        :returns: The hash
        :rtype: str
        """
        keys = [line.key for line in self._input_lines if line.key is not None]
        values = [line.value for line in self._input_lines if line.value is not None]
        return string_hash('\n'.join(keys + values))

    def get_on_blade(self, base_key, blade_number):
        """
        Get property for a particular blade
        :param base_key: Key excluding the blade number identifier
        :param blade_number: Blade number as an integer
        :return: Value of property
        """
        key = base_key + '({})'.format(blade_number)
        return self[key]

    def set_on_blade(self, base_key, blade_number, value):
        """
        Set property on a particular blade
        :param base_key: Key excluding the blade number identifier
        :param blade_number: Blade number as an integer
        :param value: Value to set
        """
        key = base_key + '({})'.format(blade_number)
        self[key] = value

    def __getitem__(self, key):
        parts = key.split(self._key_separator, maxsplit=1)
        line = self._get_line(parts[0])
        if len(parts) > 1:
            return self._get_nested_input(line)[parts[1]]
        return line.value.strip('"')

    def __setitem__(self, key, value):
        parts = key.split(self._key_separator, maxsplit=1)
        line = self._get_line(parts[0])
        if len(parts) > 1:
            self._get_nested_input(line)[parts[1]] = value
        else:
            line.value = str(value).strip('"')

    def _get_line(self, key, nth_line=1):
        """
        Get input line based on key
        :param key: Identifying key of input line
        :param nth_line: If key is duplicated in input, return the line corresponding to the 'nth" occurrence of the key
        :return: Line from self._input_lines container
        """
        generate = (line for line in self._input_lines if line.key == key)
        try:
            if nth_line == 1:
                return next(generate)
            else:
                for _ in range(nth_line):
                    line = next(generate)
                return line
        except StopIteration:
            raise KeyError('parameter \'{}\' not found'.format(key))

    def _get_nested_input(self, line):
        if line.key not in self._nested_inputs:
            self._nested_inputs[line.key] = NRELSimulationInput.from_file(line.value)
        return self._nested_inputs[line.key]

    def _get_index(self, key):
        for i, line in enumerate(self._input_lines):
            if line and line.key == key:
                return i
        raise KeyError('parameter \'{}\' not found'.format(key))

    def _get_indices_if(self, pred):
        lines = []
        for i, line in enumerate(self._input_lines):
            if pred(line.key):
                lines.append(i)
        return lines

    def _absolutise_paths(self, root_folder, lines):
        for i in lines:
            rel_path = self._input_lines[i].value
            if rel_path:
                self._input_lines[i].value = path.abspath(path.join(root_folder, rel_path))

    @staticmethod
    def _lines_with_paths():
        return []


class TurbsimInput(NRELSimulationInput):
    """
    Handles contents of TurbSim (FAST wind generation) input file
    """
