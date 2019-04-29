import pytest
from os import path

import luigi

from spawnwind.nrel.nrel_input_line import NrelInputLine
from spawnwind.nrel.wind_input import InflowWindInput


@pytest.fixture(scope='function')
def inflow_wind_input(inflowwind_input_file, wind_gen_spawner):
    with open(inflowwind_input_file, 'r') as fp:
        lines = [NrelInputLine(line) for line in fp.readlines()]
    return InflowWindInput(lines, path.dirname(path.abspath(inflowwind_input_file)), wind_gen_spawner)


@pytest.mark.parametrize('type_,line_number', [
    (2, 16),
    (3, 20),
    (4, 22)
])
def test_inflow_wind_input_edits_right_filename(inflow_wind_input, type_, line_number, tmpdir):
    inflow_wind_input['WindType'] = type_
    inflow_wind_input.wind_file = 'very/windy.wnd'
    assert inflow_wind_input.wind_file == 'very/windy.wnd'
    file_path = path.join(tmpdir, 'inflow.inp')
    inflow_wind_input.to_file(path.join(file_path))
    with open(file_path, 'r') as fp:
        lines = fp.readlines()
    assert '"very/windy.wnd"' in lines[line_number-1]


def test_wind_type_is_correct(inflow_wind_input):
    assert inflow_wind_input.wind_type == 'uniform'
    inflow_wind_input.wind_type = 'turbsim'
    assert inflow_wind_input.wind_type == 'turbsim'
    inflow_wind_input.wind_type = 'bladed'
    assert inflow_wind_input.wind_type == 'bladed'


def test_produces_right_tasks(inflow_wind_input, tmpdir):
    inflow_wind_input.wind_type = 'uniform'
    assert len(inflow_wind_input.get_wind_gen_tasks(tmpdir, {})) == 0

    inflow_wind_input.wind_type = 'turbsim'
    tasks = inflow_wind_input.get_wind_gen_tasks(tmpdir, {})
    assert len(tasks) == 1
    assert path.splitext(tasks[0].wind_file_path)[1] == '.bts'

    inflow_wind_input.wind_type = 'bladed'
    tasks = inflow_wind_input.get_wind_gen_tasks(tmpdir, {})
    assert len(tasks) == 1
    assert path.splitext(tasks[0].wind_file_path)[1] == '.wnd'


@pytest.mark.parametrize('wind_type', [
    'bladed',
    'turbsim'
])
def test_wind_spawner_produces_output(inflow_wind_input, wind_type, tmpdir):
    inflow_wind_input.wind_type = wind_type
    inflow_wind_input.wind_speed = 8.0
    inflow_wind_input.turbulence_intensity = 0.12
    tasks = inflow_wind_input.get_wind_gen_tasks(tmpdir, {})
    luigi.build(tasks, local_scheduler=True, log_level='WARNING')
    for t in tasks:
        assert path.isfile(t.wind_file_path)
