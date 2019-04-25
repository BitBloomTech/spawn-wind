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
    def __init__(self, input_lines, root_folder):
        """Initialises :class:`NRELSimulationInput`

        :param input_lines: The lines of the input file
        :type input_lines: list
        :param root_folder: The root folder containing the input file
        :type root_folder: path-like
        """
        self._input_lines = input_lines
        self._absolutise_paths(root_folder, self._lines_with_paths())

    @classmethod
    def from_file(cls, file_path):
        """Creates a :class:`NRELSimulationInput` by loading a file

        :param file_path: The file path to load
        :type file_path: path-like

        :returns: The simulation input object
        :rtype: An instance of :class:`NRELSimulationInput`
        """
        with open(file_path, 'r') as fp:
            input_lines = fp.readlines()
        root_folder = path.abspath(path.split(file_path)[0])
        return cls([NrelInputLine(line) for line in input_lines], root_folder)

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

    def __setitem__(self, key, value):
        self._get_line(key).value = str(value).strip('"')

    def __getitem__(self, key):
        return self._get_line(key).value.strip('"')

    def _get_line(self, key, n=1):
        generate = (line for line in self._input_lines if line.key == key)
        try:
            if n == 1:
                return next(generate)
            else:
                for _ in range(n):
                    line = next(generate)
                return line
        except StopIteration:
            raise KeyError('parameter \'{}\' not found'.format(key))

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
    """Handles contents of TurbSim (FAST wind generation) input file"""

