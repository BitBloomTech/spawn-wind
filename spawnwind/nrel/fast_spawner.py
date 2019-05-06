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
from os import path
import copy

from spawn.util import quote

from ..spawners import AeroelasticSimulationSpawner
from .tasks import FastSimulationTask


# pylint: disable=too-many-public-methods
class FastSimulationSpawner(AeroelasticSimulationSpawner):
    """Spawns FAST simulation tasks with wind generation dependency if necessary"""

    def __init__(self, fast_input, wind_spawner, prereq_outdir):
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
        self._wind_input = fast_input.get_wind_input(wind_spawner)
        self._elastodyn_input = self._input.get_elastodyn_input()
        self._blade_range = list(range(1, self.get_number_of_blades()))
        self._servodyn_input = self._input.get_servodyn_input(self._blade_range)
        # intermediate parameters
        self._pitch_manoeuvre_rate = None
        self._yaw_manoeuvre_rate = None

    def spawn(self, path_, metadata):
        """Spawn a simulation task

        :param path_: The output path for the task
        :type path_: str
        :param metadata: Metadata to add to the task
        :type metadata: dict

        :returns: The simulation task
        :rtype: :class:`SimulationTask`
        """
        if not path.isabs(path_):
            raise ValueError('Must provide an absolute path')
        if not path.isdir(path_):
            os.makedirs(path_)
        wind_tasks = self._wind_input.get_wind_gen_tasks(self._prereq_outdir, metadata)
        self._write_linked_module_input(self._wind_input, path_)
        self._write_linked_module_input(self._elastodyn_input, path_)
        self._write_linked_module_input(self._servodyn_input, path_)
        sim_input_file = path.join(path_, 'fast.input')
        self._input.to_file(sim_input_file)
        sim_task = FastSimulationTask(
            'run ' + path_,
            _input_file_path=sim_input_file,
            _dependencies=wind_tasks,
            _metadata=metadata
        )
        return sim_task

    def _write_linked_module_input(self, module, path_):
        if hasattr(module, 'key'):
            self._input[module.key] = module.to_file(path.join(path_, module.key + '.input'))

    def branch(self):
        """Create a copy of this spawner

        :returns: A copy of this spawner with all values equal
        :rtype: :class:`FastSimulationSpawner`
        """
        branched_spawner = copy.copy(self)
        # pylint: disable=protected-access
        branched_spawner._input = copy.deepcopy(self._input)
        branched_spawner._wind_spawner = self._wind_spawner.branch()
        return branched_spawner

    # Simulation options
    # pylint: disable=missing-docstring
    def get_output_start_time(self):
        return float(self._input['TStart'])

    # pylint: disable=missing-docstring
    def set_output_start_time(self, time):
        delta = time - self.get_output_start_time()
        self._input['TStart'] = time
        self._input['TMax'] = float(self._input['TMax']) + delta  # Adjust max time so that simulation time is constant
        self._wind_spawner.duration = float(self._input['TMax'])

    # pylint: disable=missing-docstring
    def get_simulation_time(self):
        return float(self._input['TMax']) - self.get_output_start_time()

    # pylint: disable=missing-docstring
    def set_simulation_time(self, time):
        total_time = float(time) + self.get_output_start_time()
        self._input['TMax'] = float(time) + self.get_output_start_time()
        self._wind_spawner.analysis_time = time
        self._wind_spawner.duration = total_time

    # Initial Conditions
    # pylint: disable=missing-docstring
    def get_initial_rotor_speed(self):
        return float(self._elastodyn_input['RotSpeed'])

    # pylint: disable=missing-docstring
    def set_initial_rotor_speed(self, rotor_speed):
        self._elastodyn_input['RotSpeed'] = rotor_speed

    # pylint: disable=missing-docstring
    def get_initial_azimuth(self):
        return float(self._elastodyn_input['Azimuth'])

    # pylint: disable=missing-docstring
    def set_initial_azimuth(self, azimuth):
        self._elastodyn_input['Azimuth'] = azimuth

    # pylint: disable=missing-docstring
    def get_initial_yaw(self):
        return float(self._elastodyn_input['NacYaw'])  # 'YawNeut' could be another possibility here

    # pylint: disable=missing-docstring
    def set_initial_yaw(self, angle):
        self._elastodyn_input['NacYaw'] = angle

    # pylint: disable=missing-docstring
    def get_initial_pitch(self):
        raise NotImplementedError()

    # pylint: disable=missing-docstring
    def set_initial_pitch(self, angle):
        for bld_num in self._blade_range:
            self.set_blade_initial_pitch(bld_num, angle)

    # pylint: disable=missing-docstring
    def get_blade_initial_pitch(self, index):
        return float(self._elastodyn_input.get_on_blade('BlPitch', index))

    # pylint: disable=missing-docstring
    def set_blade_initial_pitch(self, index, angle):
        self._elastodyn_input.set_on_blade('BlPitch', index, angle)
        self._servodyn_input.reconcile_pitch_manoeuvre(index, angle)

    # Supervisory operation
    # pylint: disable=missing-docstring
    def get_operation_mode(self):
        raise NotImplementedError('Incapable of determining operation mode')  # this is a tricky one!

    # pylint: disable=missing-docstring
    def set_operation_mode(self, mode):
        if mode not in ['normal', 'idling', 'parked']:
            raise ValueError('mode \'' + mode + '\' unrecognised')

        # Generator
        large_time = self._make_large_time()
        if mode == 'normal':
            self._servodyn_input['GenTiStr'] = True
            self._servodyn_input['TimGenOn'] = 0.0  # time to turn generator on
            self._servodyn_input['TimGenOf'] = large_time  # never turn generator off
            self._free_pitch()
        else:
            self._servodyn_input['GenTiStr'] = True
            self._servodyn_input['TimGenOn'] = large_time  # never turn generator on
            self._servodyn_input['TimGenOf'] = 0.0  # time to turn generator off
            self._fix_pitch()

        # rotor freedom
        if mode in ['normal', 'idling']:
            self._elastodyn_input['GenDOF'] = True
        else:
            self._elastodyn_input['GenDOF'] = False
        if mode in ['idling', 'parked']:
            self.initial_rotor_speed = 0.0

    # pylint: disable=missing-docstring
    def get_pitch_manoeuvre_time(self):
        raise NotImplementedError('Incapable of determining pitch manoeuvre time for all blades at once')

    # pylint: disable=missing-docstring
    def set_pitch_manoeuvre_time(self, time):
        for bld_num in self._blade_range:
            self.set_blade_pitch_manoeuvre_time(bld_num, time)

    # pylint: disable=missing-docstring
    def get_blade_pitch_manoeuvre_time(self, index):
        return self._servodyn_input.get_blade_pitch_manoeuvre_time(index)

    # pylint: disable=missing-docstring
    def set_blade_pitch_manoeuvre_time(self, index, time):
        self._servodyn_input.set_blade_pitch_manoeuvre_time(index, time)
        self._servodyn_input.reconcile_pitch_manoeuvre(index, self.get_blade_initial_pitch(index))

    # pylint: disable=missing-docstring
    def get_pitch_manoeuvre_rate(self):
        return self._servodyn_input.pitch_manoeuvre_rate

    # pylint: disable=missing-docstring
    def set_pitch_manoeuvre_rate(self, pitch_rate):
        self._servodyn_input.pitch_manoeuvre_rate = pitch_rate
        for bld_num in self._blade_range:
            self._servodyn_input.reconcile_pitch_manoeuvre(bld_num, self.get_blade_initial_pitch(bld_num))

    # pylint: disable=missing-docstring
    def get_final_pitch(self):
        return self._servodyn_input.final_pitch

    # pylint: disable=missing-docstring
    def set_final_pitch(self, angle):
        self._servodyn_input.final_pitch = angle
        for bld_num in self._blade_range:
            self._servodyn_input.reconcile_pitch_manoeuvre(bld_num, self.get_blade_initial_pitch(bld_num))

    # pylint: disable=missing-docstring
    def get_blade_final_pitch(self, index):
        return self._servodyn_input.get_blade_final_pitch(index)

    # pylint: disable=missing-docstring
    def set_blade_final_pitch(self, index, angle):
        self._servodyn_input.set_blade_final_pitch(index, angle)
        self._servodyn_input.reconcile_pitch_manoeuvre(index, self.get_blade_initial_pitch(index))

    # pylint: disable=missing-docstring
    def get_pitch_control_start_time(self):
        return self._servodyn_input.pitch_control_start_time

    # pylint: disable=missing-docstring
    def set_pitch_control_start_time(self, time):
        self._servodyn_input.pitch_control_start_time = time

    # pylint: disable=missing-docstring
    def get_yaw_manoeuvre_time(self):
        return self._servodyn_input.yaw_manoeuvre_time

    # pylint: disable=missing-docstring
    def set_yaw_manoeuvre_time(self, time):
        self._servodyn_input.yaw_manoeuvre_time = time

    # pylint: disable=missing-docstring
    def get_yaw_manoeuvre_rate(self):
        return self._servodyn_input.yaw_manoeuvre_rate

    # pylint: disable=missing-docstring
    def set_yaw_manoeuvre_rate(self, rate):
        self._servodyn_input.yaw_manoeuvre_rate = rate
        self._servodyn_input.reconcile_yaw_manoeuvre(self.initial_yaw)

    # pylint: disable=missing-docstring
    def get_final_yaw(self):
        return self._servodyn_input.final_yaw

    # pylint: disable=missing-docstring
    def set_final_yaw(self, angle):
        self._servodyn_input.final_yaw = angle
        self._servodyn_input.reconcile_yaw_manoeuvre(self.initial_yaw)

    # Turbine faults
    # pylint: disable=missing-docstring
    def get_grid_loss_time(self):
        return float(self._servodyn_input['TimGenOf'])

    # pylint: disable=missing-docstring
    def set_grid_loss_time(self, time):
        self._servodyn_input['GenTiStp'] = True
        self._servodyn_input['TimGenOf'] = time

    # Properties deferred to wind input:
    # pylint: disable=missing-docstring
    def get_wind_type(self):
        return self._wind_input.wind_type

    # pylint: disable=missing-docstring
    def set_wind_type(self, wind_type):
        self._wind_input.wind_type = wind_type

    # pylint: disable=missing-docstring
    def get_wind_speed(self):
        return self._wind_input.wind_speed

    # pylint: disable=missing-docstring
    def set_wind_speed(self, speed):
        self._wind_input.wind_speed = speed

    # pylint: disable=missing-docstring
    def get_turbulence_intensity(self):
        return self._wind_input.turbulence_intensity

    # pylint: disable=missing-docstring
    def set_turbulence_intensity(self, turbulence_intensity):
        self._wind_input.turbulence_intensity = turbulence_intensity

    # pylint: disable=missing-docstring
    def get_turbulence_seed(self):
        return self._wind_input.turbulence_seed

    # pylint: disable=missing-docstring
    def set_turbulence_seed(self, seed):
        self._wind_input.turbulence_seed = seed

    # pylint: disable=missing-docstring
    def get_wind_shear(self):
        return self._wind_input.wind_shear

    # pylint: disable=missing-docstring
    def set_wind_shear(self, exponent):
        self._wind_input.wind_shear = exponent

    # pylint: disable=missing-docstring
    def get_upflow(self):
        return self._wind_input.upflow

    # pylint: disable=missing-docstring
    def set_upflow(self, angle):
        self._wind_input.upflow = angle

    # pylint: disable=missing-docstring
    def get_wind_file(self):
        return self._wind_input.wind_file

    # pylint: disable=missing-docstring
    def set_wind_file(self, file):
        self._wind_input.wind_file = os.path.abspath(file)

    # Properties of turbine, for which setting is not supported
    def get_number_of_blades(self):
        return int(self._elastodyn_input['NumBl'])

    # non-properties
    def _fix_pitch(self, pitch_angle=None):
        if pitch_angle is not None:
            self.initial_pitch = pitch_angle
        self._servodyn_input.pitch_manoeuvre_rate = 0.0
        for bld_num in self._blade_range:
            self._servodyn_input.reconcile_pitch_manoeuvre(bld_num, self.get_blade_initial_pitch(bld_num))

    def _free_pitch(self):
        large_time = self._make_large_time()
        for bld_num in self._blade_range:
            self._servodyn_input.set_blade_pitch_manoeuvre_time(bld_num, large_time)

    def _make_large_time(self):
        return max(9999.9, float(self._input['TMax']) + 1.0)
