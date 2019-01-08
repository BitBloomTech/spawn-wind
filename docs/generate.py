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
import os

import shutil

from sphinx.cmd.build import build_main as build

GENERATED_RSTS = [
    'spawnwind.spawners'
]

TITLES = {
    'spawnwind.spawners': 'Spawners'
}

def rst_contents(module):
    title = TITLES.get(module, module)
    underline = '='*len(title)
    return f'{title}\n{underline}\n\n.. automodule:: {module}\n\t:members:\n\t:imported-members:\n'

SUMMARY = """Spawner Reference
=================

.. autosummary::

    {}
"""

def summary():
    return SUMMARY.format('\n    '.join(GENERATED_RSTS))

def generate():
    docs_dir = os.path.join(os.getcwd(), 'docs')
    build_dir = os.path.join(docs_dir, '_build')
    spawner_docs_dir = os.path.join(docs_dir, 'spawner')
    if os.path.isdir(spawner_docs_dir):
        shutil.rmtree(spawner_docs_dir)
    os.mkdir(spawner_docs_dir)
    for file in GENERATED_RSTS:
        with open(os.path.join(spawner_docs_dir, file + '.rst'), 'w+') as fp:
            fp.write(rst_contents(file))
    build([docs_dir, build_dir])

if __name__ == '__main__':
    generate()