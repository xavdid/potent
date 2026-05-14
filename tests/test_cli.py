import re
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from cyclopts import CycloptsError
from pydantic import ValidationError

from potent.cli import app as cli
from potent.operations.raw_command import RawCommand
from potent.plan import CommandConfig, Plan


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


@patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0))
def test_auto_reset_plans(mock_run: MagicMock, tmp_path):
    plan_path = tmp_path / "example.plan.json"

    sub_path = tmp_path / "cool"
    sub_path.mkdir()

    plan_path.write_text(
        Plan(
            operations=[RawCommand(config=RawCommand.OpConfig(arguments=["pwd"]))],
            directories=[sub_path],
            config=CommandConfig(),
        ).model_dump_json()
    )

    result = cli(
        ["run", str(plan_path)], result_action="return_int_as_exit_code_else_zero"
    )
    assert result == 0
    # runs normally
    assert mock_run.call_count == 1

    p = Plan.from_path(plan_path)
    assert p.config.mode == "command"
    assert p.config.last_run == date.today()
    assert list(p.operations[0].directory_statuses.values()) == ["completed"]

    result = cli(
        ["run", str(plan_path)], result_action="return_int_as_exit_code_else_zero"
    )
    assert result == 0
    # doesn't get run again
    assert mock_run.call_count == 1

    # last run is now yesterday
    p.config.last_run = date.today() - timedelta(days=1)
    plan_path.write_text(p.model_dump_json())

    # running again now resets it
    result = cli(
        ["run", str(plan_path)], result_action="return_int_as_exit_code_else_zero"
    )
    assert result == 0
    # shells out again
    assert mock_run.call_count == 2

    p = Plan.from_path(plan_path).config.last_run == date.today()  # type:ignore
