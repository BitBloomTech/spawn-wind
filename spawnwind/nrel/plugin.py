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
"""Defines the :mod:`mutliwindcalc` plugin for nrel
"""
from os import path

from luigi import configuration

from spawn.util.validation import validate_file, validate_dir

from .simulation_input import TurbsimInput, FastInput
from .turbsim_spawner import TurbsimSpawner
from .fast_spawner import FastSimulationSpawner
from .tasks import WindGenerationTask, FastSimulationTask

def create_spawner(turbsim_exe, fast_exe, turbsim_base_file, fast_base_file, runner_type, turbsim_working_dir, fast_working_dir, outdir, prereq_outdir):
    """Creates an nrel spawner
    """
    validate_file(turbsim_exe, 'turbsim_exe')
    validate_file(fast_exe, 'fast_exe')
    validate_file(turbsim_base_file, 'turbsim_base_file')
    validate_file(fast_base_file, 'fast_base_file')
    validate_dir(turbsim_working_dir, 'turbsim_working_dir')
    validate_dir(fast_working_dir, 'fast_working_dir')

    luigi_config = configuration.get_config()

    luigi_config.set(WindGenerationTask.__name__, '_exe_path', turbsim_exe)
    luigi_config.set(WindGenerationTask.__name__, '_runner_type', runner_type)
    luigi_config.set(WindGenerationTask.__name__, '_working_dir', turbsim_working_dir)
    luigi_config.set(FastSimulationTask.__name__, '_exe_path', fast_exe)
    luigi_config.set(FastSimulationTask.__name__, '_runner_type', runner_type)
    luigi_config.set(FastSimulationTask.__name__, '_working_dir', fast_working_dir)

    wind_spawner = TurbsimSpawner(TurbsimInput.from_file(turbsim_base_file))
    return FastSimulationSpawner(FastInput.from_file(fast_base_file), wind_spawner, path.join(outdir, prereq_outdir))


def NTM(Iref, wind_speed):
    """Evaluates turbulence intensity according to normal turbulence model"""
    return Iref * (0.75 * wind_speed + 5.6) / wind_speed


def ETM(Iref, Vmean, wind_speed):
    """Evaluates turbulence intensity according to extreme turbulence model"""
    c = 2.0
    return c * Iref * (0.072 * (Vmean / c + 3.0) * (wind_speed / c - 4) + 10.0) / wind_speed

