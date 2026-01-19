from pathlib import Path
from unittest.mock import patch

import pytest

from potent.operations._base import ensure_directory
from potent.operations.raw_command import Config, RawCommand
from potent.plan import Plan


@pytest.fixture
def path_with_tilde():
    # dynamically read a directory in my home folder and ensure it validates
    dir_in_home = str(next(p for p in Path.home().iterdir() if p.is_dir()))

    return Path(dir_in_home.replace(str(Path.home()), "~"))


@patch("subprocess.run")
def test_os_errors_handled(mock_run, tmp_path: Path):
    mock_run.side_effect = FileNotFoundError(
        "[Errno 2] No such file or directory: 'cool'"
    )

    result = RawCommand(config=Config(arguments=[])).run(tmp_path)

    # should fail, but not throw
    assert result.success is False


def test_requires_absolute_path(tmp_path: Path):
    assert ensure_directory(tmp_path) == tmp_path


def test_supports_path_with_home(path_with_tilde: Path):
    assert ensure_directory(path_with_tilde) == path_with_tilde


def test_home_file_doesnt_work(path_with_tilde: Path):
    file_in_home = str(next(p for p in Path.home().iterdir() if p.is_file()))

    path_with_tilde = Path(file_in_home.replace(str(Path.home()), "~"))

    with pytest.raises(ValueError):
        ensure_directory(path_with_tilde)


def test_tile_paths_are_retained_when_dumping_plan(path_with_tilde: Path):
    plan = Plan(operations=[], directories=[path_with_tilde])
    print(plan)

    assert str(path_with_tilde) in plan.model_dump_json()
