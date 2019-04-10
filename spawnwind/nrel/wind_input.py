from os import path
from .simulation_input import NRELSimulationInput


class WindInput(NRELSimulationInput):
    @property
    def key(self):
        """Key im primary FAST input file"""
        raise NotImplementedError()

    def write(self, directory):
        """Write input file into directory, returning full path of written file"""
        raise NotImplementedError()

    def get_wind_file(self):
        raise NotImplementedError()

    def set_wind_file(self, file):
        raise NotImplementedError()


class AerodynInput(WindInput):
    """Handles contents of Aerodyn (FAST aerodynamics) input file, which defines wind input for versions < 8.12"""

    def _lines_with_paths(self):
        num_foils = int(self['NumFoil'])
        index = self._get_index('FoilNm')
        return range(index, index + num_foils)

    @property
    def key(self):
        return 'ADFile'

    def write(self, directory):
        aerodyn_file_path = path.join(directory, 'aerodyn.ipt')
        self.to_file(aerodyn_file_path)
        return aerodyn_file_path

    def get_wind_file(self):
        return self['WindFile']

    def set_wind_file(self, file):
        self['WindFile'] = file


class InflowWindInput(WindInput):
    """Handles contents of InflowWind input file which handles wind input of FAST in versions >= 8.12"""

    def _lines_with_paths(self):
        keys = ['Filename', 'FilenameRoot', 'FileName_u', 'FileName_v', 'FileName_w']
        return [self._get_index(k) for k in keys]

    @property
    def key(self):
        return 'InflowFile'

    def write(self, directory):
        file_path = path.join(directory, 'InflowWind.ipt')
        self.to_file(file_path)
        return file_path

    def get_wind_file(self):
        return self._get_wind_file_line().value

    def set_wind_file(self, file):
        self._get_wind_file_line().value = file

    def _get_wind_file_line(self):
        type_ = int(self['WindType'])
        if type_ == 2:
            return self._get_line('Filename')
        elif type_ == 3:
            return self._get_line('Filename', 2)
        elif type_ == 4:
            return self._get_line('FilenameRoot')
        else:
            raise KeyError('Cannot set wind file in InflowWind, type_={}'.format(type_))

