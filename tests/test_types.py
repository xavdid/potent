from pathlib import Path

import pytest

from potent.commands._types import get_command_dir, is_plan_json


@pytest.mark.parametrize(
    ["path", "success"], [[Path("cool"), False], [Path("cool.plan.json"), True]]
)
def test_is_plan_json(path: Path, success: bool):
    if success:
        assert is_plan_json(None, path) is None
    else:
        with pytest.raises(ValueError):
            is_plan_json(None, path)


def test_get_command_dir_default():
    assert get_command_dir() == Path().home() / ".config" / "potent" / "commands"


def test_get_command_dir_xdg(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert get_command_dir() == tmp_path / "potent" / "commands"
