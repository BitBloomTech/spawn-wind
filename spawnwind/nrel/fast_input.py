"""
Handlers of Main FAST input file
"""
from .wind_input import AerodynInput, InflowWindInput
from .simulation_input import NRELSimulationInput
from .servo_input import Fast7ServoInput, ServoDynInput


class ElastoDynInput(NRELSimulationInput):
    """
    Input handler for ElastoDyn (v8.12 and later)
    """
    key = 'EDFile'

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key not in ['OutFile', 'DLL_FileName']
        return self._get_indices_if(is_file_path)


class FastInput(NRELSimulationInput):
    """
    Base class manager for main FAST input file
    """
    def get_wind_input(self, wind_gen_spawner):
        """
        :param wind_gen_spawner: Spawner of wind generation tasks
        :return: `WindInput` instance for managing the contents of the input file for wind inflow
        """
        raise NotImplementedError()

    def get_servodyn_input(self, blade_range):
        """
        :param blade_range: iterable containing the numbers of the blades (e.g. [1, 2, 3])
        :return: A `FastServoInput` instance for managing control and manoeuvre inputs
        """
        raise NotImplementedError()

    def get_elastodyn_input(self):
        """
        :return: An instance responsible for handling structural inputs
        """
        raise NotImplementedError()


class Fast7Input(FastInput):
    """
    Manager for main FAST input file v7
    """
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


class Fast8Input(FastInput):
    """
    Manager for main FAST input file v8
    """
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
