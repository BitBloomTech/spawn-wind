from .wind_input import AerodynInput, InflowWindInput
from .simulation_input import NRELSimulationInput
from .servo_input import Fast7ServoInput, ServoDynInput


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

    def get_servodyn_input(self, blade_range):
        return Fast7ServoInput.from_nrel_input(self, blade_range)

    def get_elastodyn_input(self):
        return self


class Fast8Input(NRELSimulationInput):
    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFileFmt'
        return self._get_indices_if(is_file_path)

    def get_wind_input(self, wind_gen_spawner):
        return InflowWindInput.from_file(self['InflowFile'], wind_gen_spawner)

    def get_servodyn_input(self, blade_range):
        return ServoDynInput.from_nrel_input(NRELSimulationInput.from_file(self[ServoDynInput.key]), blade_range)

    def get_elastodyn_input(self):
        return ElastoDynInput.from_file(self[ElastoDynInput.key])
