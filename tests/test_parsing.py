import json
from pathlib import Path

from typer.testing import CliRunner

from potent import app

runner = CliRunner()


def test_needs_plan_json(tmp_path: Path):
    f = tmp_path / "blah.json"
    f.touch()

    result = runner.invoke(app, ["validate", str(f)])

    assert result.exit_code == 2
    # file exists, but needs a specific extension
    assert ".plan.json" in result.output


def test_validates_files(tmp_path: Path):
    f = tmp_path / "blah.plan.json"
    f.write_text(json.dumps({"steps": [], "directories": [str(tmp_path)]}))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 0
