# spawn
# Copyright (C) 2018, Simmovation Ltd.
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
"""Defines the wind generation spawners
"""
from spawn.util import FloatProperty, IntProperty
from spawn.spawners import TaskSpawner


class WindGenerationSpawner(TaskSpawner):
    """Base class for spawning wind generation tasks"""

    duration = FloatProperty(doc='Duration of the wind file in seconds', abstract=True)
    analysis_time = FloatProperty(doc='Time period in seconds on which the wind statistics are based', abstract=True)
    wind_speed = FloatProperty(doc='Mean wind speed in m/s in the longitudinal direction', abstract=True)
    turbulence_intensity = FloatProperty(doc='Turbulence intensity as a percentage ratio of wind speed standard deviation to mean wind speed', abstract=True)
    turbulence_seed = IntProperty(doc='Random number seed for turbulence generation', abstract=True)
    wind_shear = FloatProperty(doc='Vertical wind shear exponent', abstract=True)
    upflow = FloatProperty(doc='Wind inclination in degrees from the horizontal', abstract=True)
