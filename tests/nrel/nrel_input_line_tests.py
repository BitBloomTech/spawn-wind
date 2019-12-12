import pytest
from spawnwind.nrel.nrel_input_line import NrelInputLine


@pytest.mark.parametrize('line,value,key', [
    ('4  Ref      - a comment', '4', 'Ref'),
    ('3.5  Ref      - a comment', '3.5', 'Ref'),
    ('-14  Ref      - a comment', '-14', 'Ref'),
    ('Text  Ref     - a comment', 'Text', 'Ref'),
    ('"a spacey/path" ThePath   - a comment', 'a spacey/path', 'ThePath'),
    ('      "a spacey/path" ThePath   - a comment', 'a spacey/path', 'ThePath'),
    ('""  EmptyPath   - a comment', '', 'EmptyPath'),
    ('"path/to/file.txt"', 'path/to/file.txt', ''),
    ('---------------', '', '')
])
def test_key_and_value_are_correct(line, value, key):
    input_line = NrelInputLine(line)
    assert input_line.value == value
    assert input_line.key == key


@pytest.mark.parametrize('line', [
    '------------',
    ' ==============',
    '   ------section name------',
    '====== section name========',
])
def test_line_is_empty(line):
    input_line = NrelInputLine(line)
    assert not input_line


@pytest.mark.parametrize('before,new_value,after', [
    ('4  Key', '8', '8  Key'),
    ('-3.4  Key', '2.4', '2.4  Key'),
    ('"path/to/file.txt"  Key', 'new/path.txt', '"new/path.txt"  Key'),
    ('""   Key', 'something', '"something"   Key')
])
def test_inserts_value_correctly(before, new_value, after):
    input_line = NrelInputLine(before)
    input_line.value = new_value
    assert after == str(input_line)


def test_can_change_value_many_times():
    line = NrelInputLine('4   Key   - a comment')
    line.value = '8'
    assert '8' == line.value
    line.value = '-4'
    assert '-4' == line.value
    line.value = '256'
    assert '256' == line.value
    assert 'Key' == line.key
