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
    """Handles contents of Aerodyn (FAST aerodynamics) input file"""

    def _lines_with_paths(self):
        num_foils = int(self['NumFoil'])
        index, _ = self._get_index_and_parts('FoilNm')
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
