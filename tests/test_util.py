import pytest

from potent.util import table_row, truthy_list


@pytest.mark.parametrize(
    ["input_list", "expected"],
    [
        ([], []),
        ([1, 2, 3], [1, 2, 3]),
        ([1, 0, 2], [1, 2]),
        ([""], []),
        (["a", "", "b", "", "c"], ["a", "b", "c"]),
        (["a", "b", "c"], ["a", "b", "c"]),
    ],
)
def test_truthy_list(input_list, expected):
    assert truthy_list(input_list) == expected


@pytest.mark.parametrize(
    ["input_list", "expected"],
    [
        ([], "||"),
        (["a"], "|a|"),
        (["a", "b", "c"], "|a | b | c|"),
    ],
)
def test_table_row_builder(input_list, expected):
    assert table_row(input_list) == expected
