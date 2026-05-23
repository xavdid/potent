import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import rich

from potent.operations.git_status import GitStatus
from potent.operations.manual_confirmation import ManualConfirmation
from potent.operations.raw_command import RawCommand
from potent.plan import DirectoryStatus, OperationStatus, Plan, PlanStatus


@pytest.fixture
def subdirs(tmp_path) -> list[Path]:
    """
    4 subfolders that all exist
    """
    dirs = [
        (tmp_path / "a"),
        (tmp_path / "b"),
        (tmp_path / "c"),
        (tmp_path / "d"),
    ]

    for d in dirs:
        d.mkdir()

    return dirs


def test_save_path_kwarg(tmp_path):
    dest = tmp_path / "example.plan.json"
    plan = Plan(operations=[], directories=[])
    plan.save(dest)

    assert "directories" in dest.read_text()
    assert plan._path


def test_save_path_kwarg_doesnt_overwrite_stored_path(tmp_path):
    dest = tmp_path / "example.plan.json"
    dest2 = tmp_path / "example2.plan.json"

    plan = Plan(operations=[], directories=[])
    plan._path = dest
    plan.save(dest2)

    assert dest.exists() is False
    assert "directories" in dest2.read_text()
    assert plan._path == dest


def test_save_after_path_constructor(tmp_path):
    dest = tmp_path / "example.plan.json"
    dest.write_text(json.dumps({"operations": [], "directories": []}))

    plan = Plan.from_path(dest)
    assert plan._path


def test_directory_complete(subdirs):
    p = Plan(
        directories=subdirs,
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "failed",
                },
            ),
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "failed",
                },
            ),
        ],
    )

    assert p.directory_complete(subdirs[0]) is True
    assert p.directory_complete(subdirs[1]) is False
    assert p.directory_complete(subdirs[2]) is False
    assert p.directory_complete(subdirs[3]) is False


def test_reset(tmp_path: Path):
    p = Plan(
        operations=[GitStatus(directory_statuses={tmp_path: "failed"})],
        directories=[tmp_path],
    )

    assert p.directory_failed(tmp_path)

    p.reset()

    assert p.directory_pending(tmp_path)


def test_only_first_pending_dir_prints_steps(subdirs):
    assert Plan(operations=[GitStatus()], directories=subdirs).status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="not-started",
                op_results=[
                    OperationStatus(status="not-started", details=GitStatus().summary)
                ],
            ),
            *[
                DirectoryStatus(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )


def test_success_doesnt_stop_print(subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses={subdirs[0]: "completed"})],
        directories=subdirs,
    )

    assert p.status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                name=subdirs[1],
                status="not-started",
                op_results=[
                    OperationStatus(status="not-started", details=GitStatus().summary)
                ],
            ),
            *[
                DirectoryStatus(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[2:]
            ],
        ],
    )


def test_failure_always_prints(subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses=dict.fromkeys(subdirs, "failed"))],
        directories=subdirs,
    )

    assert p.status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=d,
                status="failed",
                op_results=[
                    OperationStatus(status="failed", details=GitStatus().summary)
                ],
            )
            for d in subdirs
        ],
    )


def test_failure_stops_prints(subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses={subdirs[0]: "failed"})],
        directories=subdirs,
    )

    assert p.status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="failed",
                op_results=[
                    OperationStatus(status="failed", details=GitStatus().summary)
                ],
            ),
            *[
                DirectoryStatus(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )


def test_completed_dirs_always_shown(subdirs):
    assert Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[1]: "completed",
                    subdirs[3]: "completed",
                }
            )
        ],
        directories=subdirs,
    ).status(
        just_completed_steps=[(1, subdirs[3])],
    ) == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="not-started",
                op_results=[
                    OperationStatus(status="not-started", details=GitStatus().summary)
                ],
            ),
            DirectoryStatus(
                name=subdirs[1],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                name=subdirs[2],
                status="not-started",
                op_results=[],
            ),
            DirectoryStatus(
                name=subdirs[3],
                status="completed",
                op_results=[
                    OperationStatus(status="completed", details=GitStatus().summary)
                ],
                completed_this_run=True,
            ),
        ],
        includes_run_info=True,
    )


@patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0))
def test_complex_skips_and_continues(_mock_run: MagicMock, subdirs):
    plan = Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "failed",
                },
            ),
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "failed",
                },
            ),
        ],
        directories=subdirs,
    )
    result = plan.run()

    expected = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="completed",
                op_results=[],
                completed_this_run=False,
            ),
            DirectoryStatus(
                name=subdirs[1],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectoryStatus(
                name=subdirs[2],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectoryStatus(
                name=subdirs[3],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
        ],
        includes_run_info=True,
    )

    assert result == expected


def test_comments_and_summary_are_printed_separately():
    p = Plan(
        directories=[],
        operations=[
            RawCommand(
                config=RawCommand.OpConfig(arguments=["echo", "cool"]),
                comment="ice cold",
            ),
            GitStatus(comment="all clear!"),
        ],
    )
    ops = p.outline().children[0].children

    assert len(ops) == 2
    assert "(raw-command)" in ops[0].label  # pyright: ignore[reportOperatorIssue]
    assert "echo cool" in ops[0].label  # pyright: ignore[reportOperatorIssue]
    assert len(ops[0].children) == 1
    assert "ice cold" in ops[0].children[0].label  # pyright: ignore[reportOperatorIssue]

    assert len(ops[1].children) == 1
    assert ops[1].label == "git-status"


def test_manual_confirmation_prints_comment_only_once():
    p = Plan(
        directories=[],
        operations=[
            ManualConfirmation(),
            ManualConfirmation(comment="stop!"),
        ],
    )
    ops = p.outline().children[0].children
    assert len(ops) == 2

    assert ops[0].label == "manual-confirmation"
    assert len(ops[0].children) == 0

    assert "(manual-confirmation)" in ops[1].label  # pyright: ignore[reportOperatorIssue]
    assert "stop!" in ops[1].label  # pyright: ignore[reportOperatorIssue]
    assert len(ops[1].children) == 0
