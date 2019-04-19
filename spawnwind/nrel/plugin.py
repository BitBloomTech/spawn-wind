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
"""Defines the :mod:`mutliwindcalc` plugin for nrel
"""
from os import path

from luigi import configuration

from spawn.util.validation import validate_file, validate_dir

from .simulation_input import TurbsimInput
from .fast_input import Fast7Input
from .turbsim_spawner import TurbsimSpawner
from .fast_spawner import FastSimulationSpawner
from .tasks import WindGenerationTask, FastSimulationTask

def create_spawner(
        turbsim_exe, fast_exe, turbsim_base_file, fast_base_file,
        runner_type, turbsim_working_dir, fast_working_dir, outdir, prereq_outdir
    ):
    """

    :param turbsim_exe: Location of TurbSim executable
    :param fast_exe: Location of FAST executable
    :param turbsim_base_file: Baseline TurbSim input file (typically `TurbSim.inp`)
        from which wind file generation tasks are spawned
    :param fast_base_file: FAST input file (typically `.fst`) to which all parameter
        editions are made and from which simulations are spawned
    :param runner_type: default is `process`
    :param turbsim_working_dir: Directory in which TurbSim wind generation tasks are executed
    :param fast_working_dir: Directory in which FAST simulations are executed.
        Note that the discon.dll must be in this directory
    :param outdir: Root output directory for spawning and thus where simulation outputs are located
    :param prereq_outdir: Root output directory for prerequisite tasks (i.e. wind file generation)
    :returns: `FastSimulationSpawner` object
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
    return FastSimulationSpawner(Fast7Input.from_file(fast_base_file), wind_spawner, path.join(outdir, prereq_outdir))


#pylint: disable=invalid-name
def NTM(Iref, wind_speed):
    """
    Additional evaluator - evaluates turbulence intensity according to IEC edition 3 normal turbulence model

    :param Iref: Reference turbulence intensity in percent according to turbine class
    :param wind_speed: 10-minute mean wind speed in m/s
    :returns: Turbulence intensity in percent
    """
    return Iref * (0.75 * wind_speed + 5.6) / wind_speed


#pylint: disable=invalid-name
def ETM(Iref, Vmean, wind_speed):
    """
    Additional evaluator - evaluates turbulence intensity according to IEC edition 3 extreme turbulence model

    :param Iref: Reference turbulence intensity in percent according to turbine class
    :param Vmean: Annual mean wind speed according to turbine class
    :param wind_speed: 10-minute mean wind speed in m/s
    :returns: Turbulence intensity in percent
    """
    #pylint: disable=invalid-name
    c = 2.0
    return c * Iref * (0.072 * (Vmean / c + 3.0) * (wind_speed / c - 4) + 10.0) / wind_speed
