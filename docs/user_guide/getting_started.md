# Getting Started

This page describes the main steps needed in order to run your first set of aeroelastic simulations using spawn-wind

1. Edit the `spawn.ini` file to refer to the desired FAST base input files and working directory. They are currently set up to use the NREL 5MW input files located in the `example_data/fast_input_files` directory. Note that FAST requires `discon.dll` to be in the working directory.
2. Write a Spawn input specification in JSON ([file format definition here](bad-link)). The parameters should correspond to properties of the spawner ([documented here](:ref:`Spawners`)), e.g. `wind_speed`, `simulation_time`.
   * There is an [example IEC spec](./example_data/iec_spec.json) in the repository which produces an example set of IEC load calculations. This is an example only and **not** Simmovation's official interpretation of the IEC standard so users should write their own IEC spec according to their needs and turbine.
   * Note in particular the `path` policy in the input file definition. This is used to specify the output directory of simulations.
   * Users can inspect their parameter specification and associated paths of simulations using the inspect command - `spawnwind inspect [specfile]`.
3. Execute simulations using the run command - `spawnwind run [specfile] [outdir]`