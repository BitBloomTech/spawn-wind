# Spawn Wind

This is the Simmovation Spawn Wind package, which adds FAST aeroelastic calculation to Spawn.

## Usage

```
> python spawnwind --help

Usage: spawnwind [OPTIONS] COMMAND [ARGS]...

  Command Line Interface

Options:
  --log-level [error|warning|info|debug]
                                  The log level
  --log-console                   Write logs to the console
  -d TEXT                         Definitions to override configuration file
                                  parameters (e.g. -d spawn.workers=2)
  --config-file FILE              Path to the config file.
  --help                          Show this message and exit.

Commands:
  check-config  Check the configuration.
  inspect       Expand and write to console the contents of the SPECFILE
  run           Runs the SPECFILE contents and write output to OUTDIR
  work          Adds a worker to a remote scheduler
```

See [the Spawn repository](https://github.com/Simmovation/spawn) for more information.
