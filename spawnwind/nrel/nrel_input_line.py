import re


class NrelInputLine:
    def __init__(self, line_str):
        self._line_str = line_str.lstrip()
        if self._line_str and not (self._line_str.startswith('- ') or self._line_str.startswith('--') or self._line_str[0] == '='):
            self._value_begin, self._value_end = self._find_value_indices(self._line_str)
            self._key_begin, self._key_end = self._find_key_indices(self._line_str, self._value_end)
        else:
            self._key_begin = None
            self._value_begin = None

    @staticmethod
    def _find_value_indices(line_str):
        match = re.search('^".*?"', line_str)
        if match:
            return match.start() + 1, match.end() - 1
        else:
            match = re.search('[^\s]+', line_str)
            return match.start(), match.end()

    @staticmethod
    def _find_key_indices(line_str, start):
        match = re.search('[a-zA-Z0-9_()]+', line_str[start:])
        if match is None:
            return None, None
        return start + match.start(), start + match.end()

    @property
    def key(self):
        if self._key_begin is not None:
            return self._line_str[self._key_begin:self._key_end]
        else:
            return ''

    @property
    def value(self):
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
