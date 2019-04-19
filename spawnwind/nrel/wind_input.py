from os import path
from .nrel_input_line import NrelInputLine
from .simulation_input import NRELSimulationInput


class WindInput(NRELSimulationInput):

    def __init__(self, lines, root_folder, wind_gen_spawner):
        super().__init__(lines, root_folder)
        self._wind_gen_spawner = wind_gen_spawner
        self._wind_task_cache = {}
        self._wind_is_explicit = False

    @classmethod
    def from_file(cls, file_path, wind_gen_spawner):
        with open(file_path, 'r') as fp:
            input_lines = fp.readlines()
        root_folder = path.abspath(path.split(file_path)[0])
        return cls([NrelInputLine(line) for line in input_lines], root_folder, wind_gen_spawner)

    @property
    def key(self):
        """Key im primary FAST input file"""
        raise NotImplementedError()

    def write(self, directory):
        """Write input file into directory, returning full path of written file"""
        raise NotImplementedError()

    @property
    def wind_type(self):
        raise NotImplementedError()

    @wind_type.setter
    def wind_type(self, type_):
        raise NotImplementedError()

    @property
    def wind_speed(self):
        return self._wind_gen_spawner.wind_speed

    @wind_speed.setter
    def wind_speed(self, speed):
        self._wind_gen_spawner.wind_speed = speed

    @property
    def turbulence_intensity(self):
        return self._wind_gen_spawner.turbulence_intensity

    @turbulence_intensity.setter
    def turbulence_intensity(self, turbulence_intensity):
        self._wind_gen_spawner.turbulence_intensity = turbulence_intensity

    @property
    def turbulence_seed(self):
        return self._wind_gen_spawner.turbulence_seed

    @turbulence_seed.setter
    def turbulence_seed(self, seed):
        self._wind_gen_spawner.turbulence_seed = seed

    @property
    def wind_shear(self):
        return self._wind_gen_spawner.wind_shear

    @wind_shear.setter
    def wind_shear(self, exponent):
        self._wind_gen_spawner.wind_shear = exponent

    @property
    def upflow(self):
        return self._wind_gen_spawner.upflow

    @upflow.setter
    def upflow(self, angle):
        self._wind_gen_spawner.upflow = angle

    @property
    def wind_file(self):
        return self['WindFile']

    @wind_file.setter
    def wind_file(self, file):
        self._set_wind_file(file)
        self._wind_is_explicit = True

    def _spawn_wind_gen_task(self, prereq_dir, metadata):
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

    def get_wind_gen_tasks(self, prereq_dir, metadata):
        # Generate new wind file if needed
        if self._wind_is_explicit:
            return []

        wind_task = self._spawn_wind_gen_task(prereq_dir, metadata)
        self._set_wind_file(wind_task.wind_file_path)
        return [wind_task]

    @property
    def key(self):
        return 'ADFile'

    def write(self, directory):
        aerodyn_file_path = path.join(directory, 'aerodyn.ipt')
        self.to_file(aerodyn_file_path)
        return aerodyn_file_path

    @property
    def wind_type(self):
        return 'unknown'

    @wind_type.setter
    def wind_type(self, type_):
        pass

    def _set_wind_file(self, file):
        self['WindFile'] = file

    def _lines_with_paths(self):
        num_foils = int(self['NumFoil'])
        index = self._get_index('FoilNm')
        return range(index, index + num_foils)


class InflowWindInput(WindInput):
    """Handles contents of InflowWind input file which handles wind input of FAST in versions >= 8.12"""
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
        # Generate new wind file if needed
        if self.wind_type == 'steady' or self._wind_is_explicit:
            return []

        wind_task = self._spawn_wind_gen_task(prereq_dir, metadata)
        self._set_wind_file(wind_task.wind_file_path)
        return [wind_task]

    @property
    def key(self):
        return 'InflowFile'

    def write(self, directory):
        file_path = path.join(directory, 'InflowWind.inp')
        self.to_file(file_path)
        return file_path

    @property
    def wind_type(self):
        type_num = int(self['WindType'])
        return self._wind_type_names[type_num]

    @wind_type.setter
    def wind_type(self, type_name):
        if type_name not in self._wind_type_numbers:
            raise ValueError('Invalid wind type')
        self['WindType'] = self._wind_type_numbers[type_name]

    @property
    def wind_file(self):
        return self._get_wind_file_line().value

    @wind_file.setter
    def wind_file(self, file):
        self._get_wind_file_line().value = file

    def _lines_with_paths(self):
        keys = ['Filename', 'FilenameRoot', 'FileName_u', 'FileName_v', 'FileName_w']
        return [self._get_index(k) for k in keys]

    def _get_wind_file_line(self):
        type_ = int(self['WindType'])
        if type_ == 2:
            return self._get_line('Filename')
        elif type_ == 3:
            return self._get_line('Filename', 2)
        elif type_ == 4:
            return self._get_line('FilenameRoot')
        else:
            raise KeyError('Cannot find wind file in InflowWind, type_={}'.format(type_))

