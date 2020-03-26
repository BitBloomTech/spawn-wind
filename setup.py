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
from os import path

import versioneer

PACKAGE = 'spawn-wind'

_here = path.abspath(path.dirname(__file__))

with open(path.join(_here, 'README.md')) as fp:
    README_CONTENTS = fp.read()

install_requires = [
    'spawn==0.3.0',
    'wetb==0.0.9',
    'setuptools>=38.3'
]

tests_require = [
    'pytest',
    'pytest-mock',
    'pytest-cov',
    'pylint',
    'numpy',
    'pandas',
    'tox',
    'luigi==2.8.2',
    'licensify'
]

extras_require = {
    'test': tests_require,
    'docs': ['sphinx', 'm2r'],
    'publish': ['twine']
}

setup(
    name=PACKAGE,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    packages=find_packages(exclude=('tests*',)),
    cmdclass=versioneer.get_cmdclass(),
    license='GPLv3',
    version=versioneer.get_version(),
    author='Simmovation Ltd',
    author_email='info@simmovation.tech',
    url='https://github.com/Simmovation/spawn-wind',
    platforms='any',
    description='Spawn Wind is a stand-alone extension to Simmovation\'s Spawn package designed for the specification and execution of large simulations sets of aeroelastic calculations for wind turbines',
    long_description=README_CONTENTS,
    long_description_content_type='text/markdown',
    python_requires='==3.6.*,<4',
    entry_points={
        'console_scripts': ['spawnwind=spawnwind.__main__:cli'],
    }
)
