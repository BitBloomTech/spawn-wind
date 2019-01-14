# Configuration File

The `spawn.ini` file configures spawn-wind to run with the appropriate version of FAST and TurbSim. The options are configured in syntax of `key=value` with each option on a new line. The possible options in the `[nrel]` section are as follows:

| Option | Definition |
|--------|------------|
| turbsim_exe | Location of TurbSim executable |
| fast_exe | Location of FAST executable |
| turbsim_base_file | Baseline TurbSim input file (typically `TurbSim.inp`) from which wind file generation tasks are spawned |
| fast_base_file | FAST input file (typically `.fst`) to which all parameter editions are made and from which simulations are spawned |
| turbsim_working_dir | Directory in which TurbSim wind generation tasks are executed |
| fast_working_dir | Directory in which FAST simulations are executed. Note that the discon.dll must be in this directory |
| runner_type | set to `process` |
| workers | Number of processes to run in parallel |
