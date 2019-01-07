import click

from spawn.plugins import PluginLoader
from spawn.config import DefaultConfiguration
from spawn.cli.functions import cli

import spawnwind.nrel.plugin as nrel_plugin

PluginLoader.pre_load_plugin('nrel', nrel_plugin)
DefaultConfiguration.set_default('type', 'nrel')

if __name__ == '__main__':
    cli()
