from pathlib import Path

import pytest

from potent.util import get_templates_dir, table_row, truthy_list


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
    assert table_row(*input_list) == expected


def test_get_template_dir_default():
    assert get_templates_dir() == Path().home() / ".config" / "potent" / "templates"


def test_get_template_dir_xdg(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert get_templates_dir() == tmp_path / "potent" / "templates"
