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
"""Implementation of :class:`AeroelasticSimulationSpawner` for FAST
"""
import os
import copy

from spawn.util import quote

from ..spawners import AeroelasticSimulationSpawner
from .wind_input import AerodynInput, InflowWindInput
from .tasks import FastSimulationTask

#pylint: disable=too-many-public-methods
class FastSimulationSpawner(AeroelasticSimulationSpawner):
    """Spawns FAST simulation tasks with wind generation dependency if necessary"""

    def __init__(self, fast_input, wind_spawner, prereq_outdir, version='v7'):
        """Initialises :class:`FastSimulationSpawner`

        :param fast_input: The FAST input
        :type fast_input: :class:`FastInput`
        :param wind_spawner: The TurbSim/wind calculation spawner
        :type wind_spawner: :class:`TurbsimSpawner`
        :param prereq_outdir: The output directory for prerequisites
        :type prereq_outdir: path-like
        """
        self._input = fast_input
        self._wind_spawner = wind_spawner
        self._prereq_outdir = prereq_outdir
        # non-arguments:
        if version == 'v7':
            self._wind_input = AerodynInput.from_file(self._input['ADFile'])
        else:
            self._wind_input = InflowWindInput.from_file(self._input['InflowFile'])
        self._wind_task_cache = {}
        self._wind_is_explicit = False
        # intermediate parameters
        self._pitch_manoeuvre_rate = None
        self._yaw_manoeuvre_rate = None

    def spawn(self, path, metadata):
        """Spawn a simulation task

        :param path: The output path for the task
        :type path: str
        :param metadata: Metadata to add to the task
        :type metadata: dict

        :returns: The simulation task
        :rtype: :class:`SimulationTask`
        """
        if not os.path.isabs(path):
            raise ValueError('Must provide an absolute path')
        if not os.path.isdir(path):
            os.makedirs(path)
        wind_tasks = self._spawn_preproc_tasks(metadata)
        self._input[self._wind_input.key] = self._wind_input.write(path)
        sim_input_file = os.path.join(path, 'simulation.ipt')
        self._input.to_file(sim_input_file)
        sim_task = FastSimulationTask(
            'run ' + path,
            _input_file_path=sim_input_file,
            _dependencies=wind_tasks,
            _metadata=metadata
        )
        return sim_task

    def _spawn_preproc_tasks(self, metadata):
        # Generate new wind file if needed
        if self._wind_is_explicit:
            return []

        wind_hash = self._wind_spawner.input_hash()
        if wind_hash in self._wind_task_cache:
            wind_task = self._wind_task_cache[wind_hash]
        else:
            outdir = os.path.join(self._prereq_outdir, wind_hash)
            wind_task = self._wind_spawner.spawn(outdir, metadata)
            self._wind_task_cache[wind_hash] = wind_task
        self._wind_input.set_wind_file(quote(wind_task.wind_file_path))
        return [wind_task]

    def branch(self):
        """Create a copy of this spawner

        :returns: A copy of this spawner with all values equal
        :rtype: :class:`FastSimulationSpawner`
        """
        branched_spawner = copy.copy(self)
        #pylint: disable=protected-access
        branched_spawner._input = copy.deepcopy(self._input)
        branched_spawner._wind_spawner = self._wind_spawner.branch()
        return branched_spawner

    # Simulation options
    #pylint: disable=missing-docstring
    def get_output_start_time(self):
        return float(self._input['TStart'])

    #pylint: disable=missing-docstring
    def set_output_start_time(self, time):
        delta = time - self.get_output_start_time()
        self._input['TStart'] = time
        self._input['TMax'] = float(self._input['TMax']) + delta  # Adjust max time so that simulation time is constant
        self._wind_spawner.duration = float(self._input['TMax'])

    #pylint: disable=missing-docstring
    def get_simulation_time(self):
        return float(self._input['TMax']) - self.get_output_start_time()

    #pylint: disable=missing-docstring
    def set_simulation_time(self, time):
        total_time = float(time) + self.get_output_start_time()
        self._input['TMax'] = float(time) + self.get_output_start_time()
        self._wind_spawner.analysis_time = time
        self._wind_spawner.duration = total_time

    # Initial Conditions
    #pylint: disable=missing-docstring
    def get_initial_rotor_speed(self):
        return float(self._input['RotSpeed'])

    #pylint: disable=missing-docstring
    def set_initial_rotor_speed(self, rotor_speed):
        self._input['RotSpeed'] = rotor_speed

    #pylint: disable=missing-docstring
    def get_initial_azimuth(self):
        return float(self._input['Azimuth'])

    #pylint: disable=missing-docstring
    def set_initial_azimuth(self, azimuth):
        self._input['Azimuth'] = azimuth

    #pylint: disable=missing-docstring
    def get_initial_yaw(self):
        return float(self._input['NacYaw'])  # 'YawNeut' could be another possibility here

    #pylint: disable=missing-docstring
    def set_initial_yaw(self, angle):
        self._input['NacYaw'] = angle

    #pylint: disable=missing-docstring
    def get_initial_pitch(self):
        raise NotImplementedError()

    #pylint: disable=missing-docstring
    def set_initial_pitch(self, angle):
        for i in range(self.number_of_blades):
            self.set_blade_initial_pitch(i+1, angle)

    #pylint: disable=missing-docstring
    def get_blade_initial_pitch(self, index):
        bld = self._blade_string(index)
        return float(self._input['BlPitch' + bld])

    #pylint: disable=missing-docstring
    def set_blade_initial_pitch(self, index, angle):
        bld = self._blade_string(index)
        self._input['BlPitch' + bld] = angle
        # if the pitch manoeuvre ends at time zero, the final pitch is actually the initial pitch too!
        if float(self._input['TPitManE' + bld]) <= 0.0:
            self._input['BlPitchF' + bld] = angle

    # Supervisory operation
    #pylint: disable=missing-docstring
    def get_operation_mode(self):
        raise NotImplementedError('Incapable of determining operation mode')  # this is a tricky one!

    #pylint: disable=missing-docstring
    def set_operation_mode(self, mode):
        if mode not in ['normal', 'idling', 'parked']:
            raise ValueError('mode \'' + mode + '\' unrecognised')

        # Generator
        large_time = self._make_large_time()
        if mode == 'normal':
            self._input['GenTiStr'] = True
            self._input['TimGenOn'] = 0.0  # time to turn generator on
            self._input['TimGenOf'] = large_time  # never turn generator off
            self._free_pitch()
        else:
            self._input['GenTiStr'] = True
            self._input['TimGenOn'] = large_time  # never turn generator on
            self._input['TimGenOf'] = 0.0  # time to turn generator off
            self._fix_pitch()

        # rotor freedom
        if mode in ['normal', 'idling']:
            self._input['GenDOF'] = True
        else:
            self._input['GenDOF'] = False
        if mode in ['idling', 'parked']:
            self.initial_rotor_speed = 0.0

    #pylint: disable=missing-docstring
    def get_pitch_manoeuvre_time(self):
        raise NotImplementedError('Incapable of determining pitch manoeuvre time for all blades at once')

    #pylint: disable=missing-docstring
    def set_pitch_manoeuvre_time(self, time):
        for i in range(self.number_of_blades):
            self.set_blade_pitch_manoeuvre_time(i+1, time)

    #pylint: disable=missing-docstring
    def get_blade_pitch_manoeuvre_time(self, index):
        return float(self._input['TPitManS' + self._blade_string(index)])

    #pylint: disable=missing-docstring
    def set_blade_pitch_manoeuvre_time(self, index, time):
        self._input['TPitManS' + self._blade_string(index)] = time
        self._reconcile_pitch_manoeuvre(index)

    #pylint: disable=missing-docstring
    def get_pitch_manoeuvre_rate(self):
        return self._pitch_manoeuvre_rate

    #pylint: disable=missing-docstring
    def set_pitch_manoeuvre_rate(self, pitch_rate):
        self._pitch_manoeuvre_rate = float(pitch_rate)
        for i in range(self.number_of_blades):
            self._reconcile_pitch_manoeuvre(i+1)

    #pylint: disable=missing-docstring
    def get_final_pitch(self):
        raise NotImplementedError('Incapable of determining final pitch angle for all blades at once')

    #pylint: disable=missing-docstring
    def set_final_pitch(self, angle):
        for i in range(self.number_of_blades):
            self.set_blade_final_pitch(i+1, angle)

    #pylint: disable=missing-docstring
    def get_blade_final_pitch(self, index):
        return float(self._input['BlPitchF' + self._blade_string(index)])

    #pylint: disable=missing-docstring
    def set_blade_final_pitch(self, index, angle):
        self._input['BlPitchF' + self._blade_string(index)] = angle
        self._reconcile_pitch_manoeuvre(index)

    #pylint: disable=missing-docstring
    def get_pitch_control_start_time(self):
        return float(self._input['TPCOn'])

    #pylint: disable=missing-docstring
    def set_pitch_control_start_time(self, time):
        self._input['TPCOn'] = time

    def _reconcile_pitch_manoeuvre(self, blade_number):
        if self._pitch_manoeuvre_rate is not None:
            bld = self._blade_string(blade_number)
            self._input['TPitManE' + bld] = float(self._input['TPitManS' + bld]) + \
                (float(self._input['BlPitchF' + bld]) - float(self._input['BlPitch' + bld]))\
                / self._pitch_manoeuvre_rate

    #pylint: disable=missing-docstring
    def get_yaw_manoeuvre_time(self):
        return float(self._input['TYawManS'])

    #pylint: disable=missing-docstring
    def set_yaw_manoeuvre_time(self, time):
        self._input['TYawManS'] = time
        self._input['YCMode'] = 0
        self._reconcile_yaw_manoeuvre()

    #pylint: disable=missing-docstring
    def get_yaw_manoeuvre_rate(self):
        return self._yaw_manoeuvre_rate

    #pylint: disable=missing-docstring
    def set_yaw_manoeuvre_rate(self, rate):
        self._yaw_manoeuvre_rate = float(rate)
        self._reconcile_yaw_manoeuvre()

    #pylint: disable=missing-docstring
    def get_final_yaw(self):
        return float(self._input['NacYawF'])

    #pylint: disable=missing-docstring
    def set_final_yaw(self, angle):
        self._input['NacYawF'] = angle
        self._reconcile_yaw_manoeuvre()

    def _reconcile_yaw_manoeuvre(self):
        if self._yaw_manoeuvre_rate is not None:
            self._input['TYawManE'] = self.get_yaw_manoeuvre_time() + \
                (self.get_final_yaw() - self.get_initial_yaw()) / self._yaw_manoeuvre_rate

    # Turbine faults
    #pylint: disable=missing-docstring
    def get_grid_loss_time(self):
        return float(self._input['TimGenOf'])

    #pylint: disable=missing-docstring
    def set_grid_loss_time(self, time):
        self._input['GenTiStp'] = True
        self._input['TimGenOf'] = time

    # Properties deferred to wind generation spawner:
    #pylint: disable=missing-docstring
    def get_wind_speed(self):
        return self._wind_spawner.wind_speed

    #pylint: disable=missing-docstring
    def set_wind_speed(self, speed):
        self._wind_spawner.wind_speed = speed

    #pylint: disable=missing-docstring
    def get_turbulence_intensity(self):
        return self._wind_spawner.turbulence_intensity

    #pylint: disable=missing-docstring
    def set_turbulence_intensity(self, turbulence_intensity):
        self._wind_spawner.turbulence_intensity = turbulence_intensity

    #pylint: disable=missing-docstring
    def get_turbulence_seed(self):
        return self._wind_spawner.turbulence_seed

    #pylint: disable=missing-docstring
    def set_turbulence_seed(self, seed):
        self._wind_spawner.turbulence_seed = seed

    #pylint: disable=missing-docstring
    def get_wind_shear(self):
        return self._wind_spawner.wind_shear

    #pylint: disable=missing-docstring
    def set_wind_shear(self, exponent):
        self._wind_spawner.wind_shear = exponent

    #pylint: disable=missing-docstring
    def get_upflow(self):
        return self._wind_spawner.upflow

    #pylint: disable=missing-docstring
    def set_upflow(self, angle):
        self._wind_spawner.upflow = angle

    #pylint: disable=missing-docstring
    def get_wind_file(self):
        return self._wind_input.get_wind_file()

    #pylint: disable=missing-docstring
    def set_wind_file(self, file):
        self._wind_input.set_wind_file(quote(os.path.abspath(file)))
        self._wind_is_explicit = True  # Don't generate wind task dependency

    # Properties of turbine, for which setting is not supported
    def get_number_of_blades(self):
        return int(self._input['NumBl'])

    # non-properties
    @staticmethod
    def _blade_string(blade_number):
        return '({})'.format(blade_number)

    def _fix_pitch(self, pitch_angle=None):
        if pitch_angle is not None:
            self.initial_pitch = pitch_angle
        for i in range(self.number_of_blades):
            bld = self._blade_string(i+1)
            self._input['BlPitchF' + bld] = self._input['BlPitch' + bld]
            self._input['TPitManS' + bld] = 0.0
            self._input['TPitManE' + bld] = 0.0

    def _free_pitch(self):
        large_time = self._make_large_time()
        for i in range(self.number_of_blades):
            bld = self._blade_string(i+1)
            self._input['TPitManS' + bld] = large_time
            self._input['TPitManE' + bld] = large_time

    def _set_for_all_blades(self, key, value):
        for i in range(self.number_of_blades):
            bld = self._blade_string(i+1)
            self._input[key + bld] = value

    def _make_large_time(self):
        return max(9999.9, float(self._input['TMax']) + 1.0)
