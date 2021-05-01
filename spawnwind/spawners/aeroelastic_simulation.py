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
"""Implementation of :class:`TaskSpawner` for aeroelastic simulations
"""
from spawn.util import StringProperty, IntProperty, FloatProperty, ArrayProperty, TypedProperty
from spawn.spawners import TaskSpawner

#pylint: disable=abstract-method
class AeroelasticSimulationSpawner(TaskSpawner):
    """Spawner of aeroelastic simulations of wind turbines including dependent turbulent wind file creation
    when necessary
    """

    # Simulation options
    output_start_time = FloatProperty(
        doc='Simulation time that elapses before the simulator starts logging results',
        abstract=True
    )
    simulation_time = FloatProperty(
        doc='Simulation time in seconds, excluding time before start of output',
        abstract=True
    )

    # Initial conditions
    initial_rotor_speed = FloatProperty(doc='Rotor speed at start of simulation in rpm', abstract=True)
    initial_azimuth = FloatProperty(doc='Rotor azimuth of blade 1 at start of simulation in degrees', abstract=True)
    initial_yaw = FloatProperty(
        doc='Nacelle yaw angle at start of simulation in degrees; clockwise from North',
        abstract=True
    )
    initial_pitch = FloatProperty(
        doc='Pitch angle for all blades at start of simulation; in degrees, positive towards feather',
        abstract=True
    )
    blade_initial_pitch = ArrayProperty(
        doc='Pitch angle for single blades at start of simulation; in degrees, positive towards feather',
        abstract=True, type_=float
    )

    # supervisory logic
    operation_mode = StringProperty(
        possible_values=['normal', 'idling', 'parked'],
        doc="""Operation mode:
        'normal' - power production run with generator on and rotor free
        'idling' - generator off but rotor free
        'parked' - generator off and rotor fixed
        """,
        abstract=True
    )
    controller_input_file = StringProperty(
        doc='Input file for external controller',
        abstract=True
    )

    # manoeuvres
    pitch_manoeuvre_time = FloatProperty(
        doc='Time in seconds at which all blades start a pitch manoeuvre',
        abstract=True
    )
    blade_pitch_manoeuvre_time = ArrayProperty(
        doc='Time in seconds at which one particular blade starts a pitch manoeuvre',
        abstract=True, type_=float
    )
    pitch_manoeuvre_rate = FloatProperty(doc='Pitch rate in deg/s at which pitch manoeuvre occurs', abstract=True)
    final_pitch = FloatProperty(
        doc='Pitch angle in degrees at which all blades finish after a pitch manoeuvre',
        abstract=True
    )
    blade_final_pitch = ArrayProperty(
        doc='Pitch angle in degrees at which one particular blade finishes after a pitch manoeuvre',
        abstract=True, type_=float
    )
    pitch_control_start_time = FloatProperty(doc='Time in seconds at which pitch control is initiated', abstract=True)
    yaw_manoeuvre_time = FloatProperty(doc='Time in seconds at which a yaw manoeuvre occurs', abstract=True)
    yaw_manoeuvre_rate = FloatProperty(doc='Yaw rate in deg/s at which yaw manoeuvre occurs', abstract=True)
    final_yaw = FloatProperty(
        doc='Yaw angle in degrees at which the blade finishes after a yaw manoeuvre',
        abstract=True
    )

    # faults
    grid_loss_time = FloatProperty(
        doc='Sets time in seconds for grid loss (zero generator torque) to occur',
        abstract=True
    )

    # Wind properties
    wind_type = StringProperty(doc="Input wind type, one of {'steady', 'uniform', 'turbsim'}", abstract=True)
    wind_speed = FloatProperty(doc='Mean wind speed in m/s', abstract=True)
    turbulence_intensity = FloatProperty(
        doc='Turbulence intensity as a percentage: ratio of wind speed standard deviation to mean wind speed',
        abstract=True
    )
    turbulence_seed = IntProperty(doc='Random number seed for turbulence generation', abstract=True)
    wind_shear = FloatProperty(doc='Vertical wind shear exponent', abstract=True)
    upflow = FloatProperty(doc='Wind inclination in degrees from the horizontal', abstract=True)
    wind_file = StringProperty(
        doc=(
            'Directly set the wind file for use in simulation.' +
            'This wind file must be externally generated before running tasks'
        ),
        abstract=True
    )

    # Aerodynamic settings
    wake_model_on = TypedProperty(bool, doc='Whether wake/induction model is enabled', abstract=True)
    dynamic_stall_on = TypedProperty(bool, doc='Whether dynamic stall is enabled', abstract=True)

    # Properties of turbine, for which setting is not supported
    number_of_blades = IntProperty(readonly=True, abstract=True)
