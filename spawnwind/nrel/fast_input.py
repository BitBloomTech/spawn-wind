from .wind_input import AerodynInput, InflowWindInput
from .simulation_input import NRELSimulationInput


class ServoDynInput(NRELSimulationInput):
    key = 'ServoFile'

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFile'
        return self._get_indices_if(is_file_path)


class ElastoDynInput(NRELSimulationInput):
    key = 'EDFile'

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key not in ['OutFile', 'DLL_FileName']
        return self._get_indices_if(is_file_path)


class Fast7Input(NRELSimulationInput):
    def _lines_with_paths(self):
        def is_file_path(key):
            return key in ['TwrFile', 'ADFile', 'ADAMSFile'] or 'BldFile' in key
        return self._get_indices_if(is_file_path)

    def get_wind_input(self, wind_gen_spawner):
        return AerodynInput.from_file(self['ADFile'], wind_gen_spawner)

    def get_servodyn_input(self):
        return self

    def get_elastodyn_input(self):
        return self


class Fast8Input(NRELSimulationInput):
    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFileFmt'
        return self._get_indices_if(is_file_path)

    def get_wind_input(self, wind_gen_spawner):
        return InflowWindInput.from_file(self['InflowFile'], wind_gen_spawner)

    def get_servodyn_input(self):
        return ServoDynInput.from_file(self[ServoDynInput.key])

    def get_elastodyn_input(self):
        return ElastoDynInput.from_file(self[ElastoDynInput.key])
