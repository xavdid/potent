import re
from unittest.mock import patch

import cyclopts
import pytest
from cyclopts import CycloptsError
from pydantic import ValidationError

from potent.cli import app as cli
from potent.operations.git_status import GitStatus
from potent.plan import Plan, TemplateConfig
from potent.util import get_template_runs_dir


@pytest.fixture(autouse=True)
def isolated_config(tmp_path):
    """
    isolate my actual config from these tests
    """
    toml_source = next(s for s in cli.config if isinstance(s, cyclopts.config.Toml))
    original_path = toml_source.path

    toml_source.path = tmp_path / "potent.toml"
    yield
    toml_source.path = original_path


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


@patch("potent.plan.Plan.clean_old_template_runs")
@patch("potent.plan.Path.unlink")
def test_templates_are_copied(
    mock_unlink, mock_clean, tmp_path, monkeypatch: pytest.MonkeyPatch, subdir
):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    template_plan = Plan(
        config=TemplateConfig(), operations=[GitStatus()], directories=[subdir]
    )
    template_path = tmp_path / "example.plan.json"
    template_plan.save(template_path)

    result = cli(
        ["run", str(template_path)], result_action="return_int_as_exit_code_else_zero"
    )
    assert result == 0
    assert len(list(get_template_runs_dir().iterdir())) == 1
    assert len(mock_clean.mock_calls) == 1
    # nothing to remove
    assert len(mock_unlink.mock_calls) == 0
