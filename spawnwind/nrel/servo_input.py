from .simulation_input import NRELSimulationInput


class FastServoInput(NRELSimulationInput):

    def __init__(self, blade_range, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._blade_range = blade_range

    @classmethod
    def from_nrel_input(cls, nrel_input, blade_range):
        if not isinstance(nrel_input, NRELSimulationInput):
            raise TypeError("'nrel_input' not of type 'NRELSimulationInput'")
        return cls(blade_range, nrel_input._input_lines, nrel_input._root_folder)

    # Pitch
    def get_blade_pitch_manoeuvre_time(self, blade_number):
        return float(self.get_on_blade('TPitManS', blade_number))

    def set_blade_pitch_manoeuvre_time(self, blade_number, time):
        self.set_on_blade('TPitManS', blade_number, time)

    @property
    def final_pitch(self):
        raise NotImplementedError('Incapable of determining final pitch angle for all blades at once')

    @final_pitch.setter
    def final_pitch(self, angle):
        for bld_num in self._blade_range:
            self.set_blade_final_pitch(bld_num, angle)

    def get_blade_final_pitch(self, blade_number):
        return float(self.get_on_blade('BlPitchF', blade_number))

    def set_blade_final_pitch(self, blade_number, angle):
        self.set_on_blade('BlPitchF', blade_number, angle)

    @property
    def pitch_control_start_time(self):
        return float(self['TPCOn'])

    @pitch_control_start_time.setter
    def pitch_control_start_time(self, time):
        self['TPCOn'] = time

    @property
    def pitch_manoeuvre_rate(self):
        raise NotImplementedError()

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        raise NotImplementedError()

    def get_blade_pitch_manoeuvre_end_time(self, blade_number):
        return float(self.get_on_blade('TPitManE', blade_number))

    def set_blade_pitch_manoeuvre_end_time(self, blade_number, time):
        self.set_on_blade('TPitManE', blade_number, time)

    def reconcile_pitch_manoeuvre(self, blade_number, initial_pitch):
        pass

    # Yaw
    @property
    def yaw_manoeuvre_time(self):
        return float(self['TYawManS'])

    @yaw_manoeuvre_time.setter
    def yaw_manoeuvre_time(self, time):
        self['TYawManS'] = time
        self['YCMode'] = 0

    @property
    def final_yaw(self):
        return float(self['NacYawF'])

    @final_yaw.setter
    def final_yaw(self, angle):
        self['NacYawF'] = angle

    @property
    def yaw_manoeuvre_rate(self):
        raise NotImplementedError()

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        raise NotImplementedError()

    def reconcile_yaw_manoeuvre(self, initial_yaw):
        pass


class Fast7ServoInput(FastServoInput):
    def __init__(self, *args):
        super().__init__(*args)
        self._pitch_manoeuvre_rate = None
        self._yaw_manoeuvre_rate = None

    @property
    def pitch_manoeuvre_rate(self):
        return self._pitch_manoeuvre_rate

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        self._pitch_manoeuvre_rate = float(pitch_rate)

    def reconcile_pitch_manoeuvre(self, blade_number, initial_pitch):
        if self._pitch_manoeuvre_rate:  # is not None and != 0.0
            delta_pitch = (self.get_blade_final_pitch(blade_number) - initial_pitch) / self._pitch_manoeuvre_rate
            self.set_on_blade('TPitManE', blade_number,
                              float(self.get_on_blade('TPitManS', blade_number)) + delta_pitch)
        else:
            self.set_blade_pitch_manoeuvre_end_time(blade_number, self.get_blade_pitch_manoeuvre_time(blade_number))

    @property
    def yaw_manoeuvre_rate(self):
        return self._yaw_manoeuvre_rate

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        self._yaw_manoeuvre_rate = float(rate)

    def reconcile_yaw_manoeuvre(self, initial_yaw):
        if self._yaw_manoeuvre_rate:  # is not None and != 0.0
            self['TYawManE'] = self.yaw_manoeuvre_time + \
                (self.final_yaw - initial_yaw) / self._yaw_manoeuvre_rate
        else:
            self['TYawManE'] = self['TYawManS']


class ServoDynInput(FastServoInput):
    key = 'ServoFile'

    @property
    def pitch_manoeuvre_rate(self):
        return float(self.get_on_blade('PitManRat', 1))

    @pitch_manoeuvre_rate.setter
    def pitch_manoeuvre_rate(self, pitch_rate):
        if pitch_rate != 0.0:
            for bld_num in self._blade_range:
                self.set_on_blade('PitManRat', bld_num, pitch_rate)
        else:
            # v8 does not allow zero pitch rate so set manoeuvre time to large instead
            for bld_num in self._blade_range:
                self.set_blade_pitch_manoeuvre_time(bld_num, 9999.9)

    @property
    def yaw_manoeuvre_rate(self):
        return float(self['YawManRat'])

    @yaw_manoeuvre_rate.setter
    def yaw_manoeuvre_rate(self, rate):
        self['YawManRat'] = rate

    def _lines_with_paths(self):
        def is_file_path(key):
            return 'File' in key and key != 'OutFile'
        return self._get_indices_if(is_file_path)
