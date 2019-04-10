import pytest
from os import path

from spawnwind.nrel.nrel_input_line import NrelInputLine
from spawnwind.nrel.wind_input import InflowWindInput


@pytest.mark.parametrize('type_,line_number', [
    (2, 16),
    (3, 20),
    (4, 22)
])
def test_inflow_wind_input_edits_right_filename(example_data_folder, type_, line_number, tmpdir):
    filename = path.join(example_data_folder, 'fast_input_files', 'InflowWind.inp')
    with open(filename, 'r') as fp:
        lines = [NrelInputLine(line) for line in fp.readlines()]
    wind_input = InflowWindInput(lines, path.join(example_data_folder, 'fast_input_files'))
    wind_input['WindType'] = type_
    wind_input.set_wind_file('"very/windy.wnd"')
    assert wind_input.get_wind_file() == 'very/windy.wnd'
    file_path = path.join(tmpdir, 'inflow.inp')
    wind_input.to_file(path.join(file_path))
    with open(file_path, 'r') as fp:
        lines = fp.readlines()
    assert '"very/windy.wnd"' in lines[line_number-1]
