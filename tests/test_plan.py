import json
from pathlib import Path
from pprint import pprint
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest

from potent.operations._base import Status
from potent.operations.git_status import GitStatus
from potent.operations.manual_confirmation import ManualConfirmation
from potent.operations.raw_command import RawCommand
from potent.plan import DirectoryStatus, OperationStatus, Plan, PlanStatus
from potent.run_events import DirectorySkipped, DirectoryStarted, OperationCompleted


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


@pytest.fixture
def subdir(subdirs) -> Path:
    """
    1 real subfolder
    """
    return subdirs[0]


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


type HaltedTestCase = list[tuple[type[GitStatus | ManualConfirmation], Status | None]]
halted_test_cases: list[tuple[HaltedTestCase, bool]] = [
    # 0: all completed is completed, not halted
    (
        [
            (GitStatus, "completed"),
            (ManualConfirmation, "completed"),
        ],
        False,
    ),
    # 1: all failed is failed, not halted
    (
        [
            (GitStatus, "failed"),
            (ManualConfirmation, "failed"),
        ],
        False,
    ),
    # 2: first failed step is a manual confirmation, so it's halted!
    (
        [
            (GitStatus, "completed"),
            (ManualConfirmation, "failed"),
        ],
        True,
    ),
    # 3: There's a new step added, so the plan is no longer halted
    (
        [
            (GitStatus, "completed"),
            (GitStatus, None),
            (ManualConfirmation, None),
        ],
        False,
    ),
    # 4: Missing status will count as halted (we know it won't pass on run)
    (
        [
            (GitStatus, "completed"),
            (ManualConfirmation, None),
        ],
        True,
    ),
    # 5: Double halted still means halted
    (
        [
            (GitStatus, "completed"),
            (ManualConfirmation, "completed"),
            (ManualConfirmation, None),
        ],
        True,
    ),
]


@pytest.mark.parametrize(["operations", "expected"], halted_test_cases)
def test_directory_halted_completed(operations: HaltedTestCase, expected: bool, subdir):
    p = Plan(
        directories=[subdir],
        operations=[
            op(directory_statuses={subdir: status} if status else {})
            for op, status in operations
        ],
    )
    assert p.directory_halted(subdir) == expected


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
                path=subdirs[0],
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="not-started",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
                ],
            ),
            *[
                DirectoryStatus(
                    path=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )


def test_add_pending_step(subdirs):
    """
    If there's a new step added after the plan is successful, then status failed
    """
    assert Plan(
        operations=[
            GitStatus(directory_statuses=dict.fromkeys(subdirs, "completed")),
            GitStatus(),
        ],
        directories=subdirs,
    ).status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                ],
            ),
            *[
                DirectoryStatus(
                    path=d,
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
                path=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="not-started",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
                ],
            ),
            *[
                DirectoryStatus(
                    path=d,
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
                path=d,
                status="failed",
                op_results=[
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
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
                path=subdirs[0],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
                ],
            ),
            *[
                DirectoryStatus(
                    path=d,
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
                path=subdirs[0],
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="not-started",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
                ],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="not-started",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[3],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    )
                ],
                completed_this_run=True,
            ),
        ],
        includes_run_info=True,
    )


def test_halted_changes_dir(subdirs, tmp_path):
    e = Path(tmp_path / "e")
    e.mkdir()

    plan = Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "failed",
                    subdirs[2]: "completed",
                    subdirs[3]: "completed",
                }
            ),
            ManualConfirmation(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[3]: "failed",
                }
            ),
        ],
        directories=[*subdirs, e],
    )
    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="halted",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="halted",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[3],
                status="halted",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="halted",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=e,
                status="not-started",
                op_results=[
                    # TODO: probably should print, since no directory has this exact status?
                    # OperationStatus(status="not-started", details=GitStatus().summary, op_slug='git-status'),
                    # OperationStatus(
                    #     status="not-started", details=ManualConfirmation().summary,
                    # op_slug='manual-confirmation'
                    # ),
                ],
            ),
        ],
    )

    assert plan.status() == status


def test_halted_only_changes_op_that_stopped(subdirs):
    assert Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "completed",
                }
            ),
            ManualConfirmation(
                directory_statuses={
                    subdirs[1]: "completed",
                    subdirs[2]: "failed",
                }
            ),
            ManualConfirmation(),
        ],
        directories=subdirs[:3],
    ).status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="halted",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="halted",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="halted",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="completed",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                    OperationStatus(
                        status="halted",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="halted",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="halted",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
        ],
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
    result = plan.status(just_completed_steps=plan.run())

    expected = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="completed",
                op_results=[],
                completed_this_run=False,
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                        completed_this_run=True,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectoryStatus(
                path=subdirs[3],
                status="completed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                        completed_this_run=True,
                    ),
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
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
            ManualConfirmation(config=ManualConfirmation.OpConfig(reason="halt!")),
            ManualConfirmation(comment="stop!"),
        ],
    )
    ops = p.outline().children[0].children
    assert len(ops) == 3

    assert ops[0].label == "manual-confirmation"
    assert len(ops[0].children) == 0

    assert "halt!" in ops[1].label  # pyright: ignore[reportOperatorIssue]
    assert "(manual-confirmation)" in ops[1].label  # pyright: ignore[reportOperatorIssue]
    assert len(ops[1].children) == 0

    assert ops[2].label == "manual-confirmation"
    assert len(ops[2].children) == 1
    assert ops[2].children[0].label == "stop!"


def test_no_collapse_by_default(subdirs):
    plan = Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "completed",
                    subdirs[3]: "completed",
                }
            ),
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "failed",
                    subdirs[3]: "failed",
                }
            ),
            ManualConfirmation(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                }
            ),
        ],
        directories=subdirs,
    )
    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[3],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
        ],
    )

    assert plan.status() == status


def test_collapse_status_for_dupes(subdirs):
    plan = Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "completed",
                    subdirs[3]: "completed",
                }
            ),
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "failed",
                    subdirs[3]: "failed",
                }
            ),
            ManualConfirmation(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                }
            ),
        ],
        directories=subdirs,
    )
    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[1],
                status="completed",
                op_results=[],
            ),
            DirectoryStatus(
                path=subdirs[2],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            DirectoryStatus(
                path=subdirs[3],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="duplicate",
                        details="Same as `[bold cyan]c[/]`",
                        op_slug="duplicate",
                    ),
                ],
            ),
        ],
    )

    assert plan.status(collapse_duplicates=True) == status


def test_collapse_status_takes_first(subdirs):
    plan = Plan(
        operations=[
            GitStatus(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "completed",
                    subdirs[2]: "completed",
                    subdirs[3]: "completed",
                }
            ),
            GitStatus(
                directory_statuses={
                    subdirs[0]: "failed",
                    subdirs[1]: "failed",
                    subdirs[2]: "failed",
                    subdirs[3]: "failed",
                }
            ),
            ManualConfirmation(),
        ],
        directories=subdirs,
    )
    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdirs[0],
                status="failed",
                op_results=[
                    OperationStatus(
                        status="completed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="failed",
                        details=GitStatus().summary,
                        op_slug="git-status",
                    ),
                    OperationStatus(
                        status="not-started",
                        details=ManualConfirmation().summary,
                        op_slug="manual-confirmation",
                    ),
                ],
            ),
            *[
                DirectoryStatus(
                    path=s,
                    status="failed",
                    op_results=[
                        OperationStatus(
                            status="duplicate",
                            details="Same as `[bold cyan]a[/]`",
                            op_slug="duplicate",
                        ),
                    ],
                )
                for s in subdirs[1:]
            ],
        ],
    )

    assert plan.status(collapse_duplicates=True) == status


def test_renderer_is_called_with_start_and_finish(subdir: Path):
    plan = Plan(operations=[GitStatus()], directories=[subdir])

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    assert len(mock_renderer.send.mock_calls) == 2
    mock_renderer.send.assert_any_call(DirectoryStarted(path=subdir))
    mock_renderer.send.assert_any_call(
        OperationCompleted(result=ANY, path=ANY, summary=ANY, output=ANY, cmd=ANY)
    )


def test_renderer_is_called_with_start_and_skipped(subdir: Path):
    plan = Plan(
        operations=[GitStatus(directory_statuses={subdir: "completed"})],
        directories=[subdir],
    )

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    pprint(mock_renderer.send.mock_calls)
    mock_renderer.send.assert_any_call(DirectoryStarted(path=subdir))
    mock_renderer.send.assert_any_call(DirectorySkipped(path=subdir))


def test_renderer_is_called_with_halted(subdir: Path):
    plan = Plan(operations=[ManualConfirmation()], directories=[subdir])

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    mock_renderer.send.assert_called_with(
        OperationCompleted(
            result="halted",
            path=ANY,
            summary=ANY,
            output=ANY,
        )
    )
