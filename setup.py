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
from setuptools import setup, find_packages

install_requires = [
    'spawn-core',
    'wetb==0.0.9',
    'setuptools>=38.3'
]

tests_require = [
    'pytest',
    'pytest-mock',
    'pylint',
    'numpy',
    'pandas',
    'tox',
    'luigi'
]

extras_require = {
    'test': tests_require,
    'docs': ['sphinx', 'm2r'],
}

setup(
    name='spawn-wind',
    version='0.1',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    dependency_links=[
        'git+ssh://git@github.com/Simmovation/spawn.git#egg=spawn-core-0.1'
    ]
)
