import re

import pytest
from cyclopts import CycloptsError
from pydantic import ValidationError

from potent.cli import app as cli


def test_version(capsys):
    result = cli(["--version"], result_action="return_int_as_exit_code_else_zero")
    assert result == 0
    assert re.search(r"\d+\.\d+\.\d+", capsys.readouterr().out)


def test_plan_json_extension(tmp_path):
    with pytest.raises(CycloptsError) as err:
        cli(["describe", str(tmp_path / "example.json")], exit_on_error=False)
    assert "a `.plan.json` extension" in str(err)


def test_plan_must_exist(tmp_path):
    with pytest.raises(CycloptsError) as err:
        cli(["describe", str(tmp_path / "example.plan.json")], exit_on_error=False)
    assert "does not exist" in str(err)


def test_invalid_json(tmp_path):
    p = tmp_path / "example.plan.json"
    p.write_text(r"{}")
    with pytest.raises(ValidationError) as err:
        cli(["describe", str(p)], exit_on_error=False)
    assert "validation errors for Plan" in str(err)
