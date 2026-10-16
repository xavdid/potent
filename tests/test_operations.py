from pathlib import Path
from typing import cast, get_args
from unittest.mock import patch

import pytest

from potent.operations._base import (
    BaseConfig,
    BaseOperation,
    Context,
    Status,
    ensure_directory,
)
from potent.operations.git_add import GitAdd
from potent.operations.git_commit import GitCommit
from potent.operations.git_status import GitStatus
from potent.operations.git_switch import GitSwitch
from potent.operations.raw_command import RawCommand
from potent.plan import Plan
from potent.util import DataReadException


@pytest.fixture
def path_with_tilde():
    # dynamically read a directory in my home folder and ensure it validates
    dir_in_home = str(next(p for p in Path.home().iterdir() if p.is_dir()))

    return Path(dir_in_home.replace(str(Path.home()), "~"))


@patch(
    "subprocess.run",
    side_effect=FileNotFoundError("[Errno 2] No such file or directory: 'cool'"),
)
def test_os_errors_handled(_mock_run, tmp_path: Path):
    result = RawCommand(config=RawCommand.OpConfig(arguments=[])).run_and_record_result(
        tmp_path,
        Context(
            directory=tmp_path, _read_func=lambda *_: 0, _write_func=lambda *_: None
        ),
    )

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


@pytest.mark.parametrize(
    ["op", "expected"],
    [
        [GitAdd(config=GitAdd.OpConfig(all=True)), "git add (all)"],
        [GitAdd(config=GitAdd.OpConfig(pattern="*.txt")), "git add (*.txt)"],
        [
            GitCommit(config=GitCommit.OpConfig(message="Short msg")),
            'git commit -m "Short msg"',
        ],
        [
            GitCommit(
                config=GitCommit.OpConfig(
                    message="A longer message that gets truncated"
                )
            ),
            'git commit -m "A longer messag..."',
        ],
        [GitSwitch(config=GitSwitch.OpConfig(branch="asdf")), "git switch -> asdf"],
        [
            RawCommand(config=RawCommand.OpConfig(arguments=["npm", "run", "start"])),
            "npm run start (raw-command)",
        ],
        [
            RawCommand(
                config=RawCommand.OpConfig(
                    arguments=["npm", "run", "start", "--some", "arg"]
                )
            ),
            "npm run start --some arg (raw-command)",
        ],
        [
            RawCommand(
                config=RawCommand.OpConfig(
                    arguments=[
                        "npm",
                        "run",
                        "start",
                        "--some",
                        "arg",
                        "--another",
                        "arg",
                    ]
                )
            ),
            "npm run start --some arg... (raw-command)",
        ],
        [
            RawCommand(
                config=RawCommand.OpConfig(
                    name="start server",
                    arguments=["npm", "run", "start", "--some", "arg"],
                )
            ),
            "start server (raw-command)",
        ],
        [
            RawCommand(
                config=RawCommand.OpConfig(name="start server", arguments=["npm"])
            ),
            "start server (raw-command)",
        ],
        [
            RawCommand(config=RawCommand.OpConfig(arguments=["npm", "do the thing"])),
            'npm "do the thing" (raw-command)',
        ],
    ],
)
def test_summary(op: BaseOperation, expected: str):
    assert op.summary == expected


def test_only_3_statuses():
    """
    if there are more than 3 statuses, some logic (around halted status) will break
    """
    assert len(get_args(Status)) == 3


# TODO: test raw command templating
# i think it won't work because we don't recurse


def test_basic_resolving(subdir):
    op = GitSwitch(config=GitSwitch.OpConfig(branch="{{ name }}"))
    plan = Plan(
        directories=[subdir],
        operations=[op],
        data={str(subdir): {"name": "bruce"}},
    )
    resolved = plan.resolve_operation(op, subdir)

    assert resolved is not op

    assert op.is_pending(subdir)
    assert resolved.is_pending(subdir)

    assert op.config.branch == "{{ name }}"
    assert resolved.config.branch == "bruce"

    resolved.record_result(subdir, True)

    # it's important that success changes on the copy are reflected on the original
    assert resolved.is_completed(subdir)
    assert op.is_completed(subdir)


def test_noop_resolving():
    op = GitStatus()
    resolved = op._resolve(lambda _: 0)

    # ops without configs are passed through
    assert op is resolved


def test_replacement(subdir):
    op = GitSwitch(config=GitSwitch.OpConfig(branch="{{name}}"))
    trailing_space_op = GitSwitch(config=GitSwitch.OpConfig(branch="{{name }}"))
    upper_op = GitSwitch(config=GitSwitch.OpConfig(branch="{{ NAME }}"))
    plan = Plan(
        directories=[subdir],
        operations=[op, upper_op, trailing_space_op],
        data={str(subdir): {"name": "bruce", "NAME": "BRUCE"}},
    )

    for o in plan.operations:
        resolved = plan.resolve_operation(o, subdir)
        assert cast("GitSwitch", resolved).config.branch.lower() == "bruce"


def test_replacement_error(subdir):
    op = GitSwitch(config=GitSwitch.OpConfig(branch="{{name}}"))
    plan = Plan(directories=[subdir], operations=[op])

    with pytest.raises(DataReadException):
        plan.resolve_operation(op, subdir)
