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
Handling of individual lines in NREL style input files
"""
import re


class NrelInputLine:
    """
    Handles a single line of an NREL-style input file, each of which has a value, followed by a key. A key is a
    contiguous alphanumeric string and the value precedes it. Any text after a hyphen (-) is a comment, unless it's the
    first non-whitespace character (negative values) or part of a quoted string
    """

    def __init__(self, line_str):
        self._line_str = line_str.lstrip()
        if self._line_str and \
                not (self._line_str.startswith('- ') or self._line_str.startswith('--') or self._line_str[0] == '='):
            self._value_begin, self._value_end = self._find_value_indices(self._line_str)
            self._key_begin, self._key_end = self._find_key_indices(self._line_str, self._value_end)
        else:
            self._key_begin = None
            self._value_begin = None

    @staticmethod
    def _find_value_indices(line_str):
        """
        Find the indices identifying where the value lies in the input line string
        :param line_str: The input line string
        :return: Interval [start, end) as tuple identifying start and end of value string
        """
        match = re.search('^".*?"', line_str)
        if match:
            return match.start() + 1, match.end() - 1
        else:
            match = re.search(r'[^\s]+', line_str)
            return match.start(), match.end()

    @staticmethod
    def _find_key_indices(line_str, start):
        """
        Find the indices identifying where the key lies in the input line string
        :param line_str: The input line string
        :param start: Index of where to start looking for the key in the input line string
        :return: Interval [start, end) as tuple identifying start and end of key string
        """
        match = re.search('[a-zA-Z0-9_()]+', line_str[start:])
        if match is None:
            return None, None
        return start + match.start(), start + match.end()

    @property
    def key(self):
        """
        :return:  The line's key
        """
        if self._key_begin is not None:
            return self._line_str[self._key_begin:self._key_end]
        else:
            return ''

    @property
    def value(self):
        """
        :return: The line's value
        """
        if self._value_begin is not None:
            return self._line_str[self._value_begin:self._value_end]
        else:
            return ''

    @value.setter
    def value(self, new_value):
        if not isinstance(new_value, str):
            raise TypeError('New value must be string')
        self._line_str = self._line_str[:self._value_begin] + new_value + self._line_str[self._value_end:]
        length_increase = len(new_value) - self._value_end + self._value_begin
        self._value_end += length_increase
        if self._key_begin is not None:
            self._key_begin += length_increase
            self._key_end += length_increase

    def __bool__(self):
        return self._key_begin is not None and self._value_begin is not None

    def __str__(self):
        if self._line_str:
            return self._line_str
        else:
            return '\n'
