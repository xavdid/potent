import json
import re
from datetime import date, timedelta
from itertools import chain
from pathlib import Path
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest

from potent.operations._base import Status
from potent.operations.assert_branch import AssertBranch
from potent.operations.git_status import GitStatus
from potent.operations.git_switch import GitSwitch
from potent.operations.manual_confirmation import ManualConfirmation
from potent.operations.raw_command import RawCommand
from potent.plan import (
    NUM_OLD_TEMPLATE_RUNS_KEPT,
    DirectoryStatus,
    OperationStatus,
    Plan,
    PlanStatus,
    TemplateConfig,
    escape_path,
    get_available_templates,
)
from potent.run_events import (
    DirectorySkipped,
    DirectoryStarted,
    OperationFinished,
    OperationStarted,
)
from potent.util import DataReadException, get_template_runs_dir


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
        data={str(tmp_path): {"a": 1, "b": True}},
    )

    assert p.directory_failed(tmp_path)

    p.reset()

    assert p.directory_pending(tmp_path)
    assert p.data is None


def test_only_first_pending_dir_prints_steps(subdirs):
    assert Plan(operations=[GitStatus()], directories=subdirs).status(
        collapse_duplicates=True
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
            *[
                DirectoryStatus(
                    path=d,
                    status="not-started",
                    op_results=[
                        OperationStatus(
                            status="duplicate",
                            op_slug="duplicate",
                            details="Same as `[bold cyan]a[/]`",
                            completed_this_run=False,
                        ),
                    ],
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
    ).status(collapse_duplicates=True) == PlanStatus(
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
                    op_results=[
                        OperationStatus(
                            status="duplicate",
                            op_slug="duplicate",
                            details="Same as `[bold cyan]a[/]`",
                            completed_this_run=False,
                        ),
                    ],
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

    assert p.status(collapse_duplicates=True) == PlanStatus(
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
                    op_results=[
                        OperationStatus(
                            status="duplicate",
                            op_slug="duplicate",
                            details="Same as `[bold cyan]b[/]`",
                            completed_this_run=False,
                        ),
                    ],
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

    assert p.status(collapse_duplicates=False) == PlanStatus(
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

    assert p.status(collapse_duplicates=True) == PlanStatus(
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
                    op_results=[
                        OperationStatus(
                            status="duplicate",
                            op_slug="duplicate",
                            details="Same as `[bold cyan]b[/]`",
                            completed_this_run=False,
                        ),
                    ],
                )
                for d in subdirs[2:]
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
        collapse_duplicates=True,
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
                op_results=[
                    OperationStatus(
                        status="duplicate",
                        op_slug="duplicate",
                        details="Same as `[bold cyan]a[/]`",
                        completed_this_run=False,
                    ),
                ],
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
                    OperationStatus(
                        status="not-started",
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


def test_skip_collapse_status_for_dupes(subdirs):
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
                }
            ),
            ManualConfirmation(
                directory_statuses={
                    subdirs[0]: "completed",
                    subdirs[1]: "failed",
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
            *[
                DirectoryStatus(
                    path=d,
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
                        OperationStatus(
                            status="not-started",
                            details=ManualConfirmation().summary,
                            op_slug="manual-confirmation",
                        ),
                    ],
                )
                for d in subdirs[1:]
            ],
        ],
    )

    assert plan.status(collapse_duplicates=False) == status


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


def test_plans_with_gaps_before_halted_are_pending(subdir: Path):
    plan = Plan(
        operations=[
            GitStatus(directory_statuses={subdir: "completed"}),
            GitStatus(),
            ManualConfirmation(directory_statuses={subdir: "failed"}),
        ],
        directories=[subdir],
    )

    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdir,
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="completed",
                        op_slug="git-status",
                        details="git-status",
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="not-started",
                        op_slug="git-status",
                        details="git-status",
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="not-started",
                        op_slug="manual-confirmation",
                        details="manual-confirmation",
                        completed_this_run=False,
                    ),
                ],
            )
        ],
    )

    assert plan.status() == status


def test_failed_steps_dont_shadow_halted_ones(subdir: Path):
    plan = Plan(
        operations=[
            GitStatus(directory_statuses={subdir: "failed"}),
            GitStatus(),
            ManualConfirmation(directory_statuses={subdir: "failed"}),
        ],
        directories=[subdir],
    )

    status = PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdir,
                status="failed",
                op_results=[
                    OperationStatus(
                        status="failed",
                        op_slug="git-status",
                        details="git-status",
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="not-started",
                        op_slug="git-status",
                        details="git-status",
                        completed_this_run=False,
                    ),
                    OperationStatus(
                        status="not-started",
                        op_slug="manual-confirmation",
                        details="manual-confirmation",
                        completed_this_run=False,
                    ),
                ],
            )
        ],
    )

    assert plan.status() == status


def test_renderer_is_called_with_start_and_finish(subdir: Path):
    plan = Plan(operations=[GitStatus()], directories=[subdir])

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    assert len(mock_renderer.send.mock_calls) == 3
    mock_renderer.send.assert_any_call(DirectoryStarted(path=subdir))
    mock_renderer.send.assert_any_call(OperationStarted(summary=ANY, path=ANY))
    mock_renderer.send.assert_any_call(
        OperationFinished(result=ANY, path=ANY, summary=ANY, output=ANY, cmd=ANY)
    )


def test_renderer_is_called_with_start_and_skipped(subdir: Path):
    plan = Plan(
        operations=[GitStatus(directory_statuses={subdir: "completed"})],
        directories=[subdir],
    )

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    assert len(mock_renderer.send.mock_calls) == 2
    mock_renderer.send.assert_any_call(DirectoryStarted(path=subdir))
    mock_renderer.send.assert_any_call(DirectorySkipped(path=subdir))


def test_renderer_is_called_with_halted(subdir: Path):
    plan = Plan(operations=[ManualConfirmation()], directories=[subdir])

    mock_renderer = Mock()
    plan.run(renderer=mock_renderer)

    assert len(mock_renderer.send.mock_calls) == 3
    mock_renderer.send.assert_any_call(DirectoryStarted(path=subdir))
    mock_renderer.send.assert_any_call(OperationStarted(summary=ANY, path=ANY))
    mock_renderer.send.assert_any_call(
        OperationFinished(
            result="halted",
            path=ANY,
            summary=ANY,
            output=ANY,
        )
    )


def test_get_avilable_templates(tmp_path, monkeypatch: pytest.MonkeyPatch):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    templates_dir = global_dir / "potent" / "templates"
    templates_dir.mkdir(parents=True)

    basic_plan = Plan(operations=[], directories=[])

    # global templates
    basic_plan.save(templates_dir / "global_0.plan.json")
    basic_plan.save(templates_dir / "global_1.plan.json")
    (templates_dir / "fake.json").touch()  # red herring!

    # local templates
    basic_plan.save(tmp_path / "local_0.plan.json")

    # so we find the local ones
    monkeypatch.chdir(tmp_path)

    global_result, local_result = get_available_templates()

    # can't compare the output to anything directly because they all have _path set differently, so comparison fails

    assert len(global_result) == 2
    assert len(local_result) == 1

    for p in chain(*get_available_templates()):
        assert p.directories == []
        assert p.operations == []
        assert p.comment is None
        assert p._path
        assert re.search(r"(local|global)_\d\.plan\.json", p._path.name)


@patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0))
def test_assert_runs_every_time(mock_subprocess: MagicMock, subdir):
    plan = Plan(
        operations=[
            AssertBranch(config=AssertBranch.OpConfig(branch="")),
            ManualConfirmation(),
        ],
        directories=[subdir],
    )
    plan.run()
    plan.run()
    plan.run()

    # assert is called on every run
    assert len(mock_subprocess.mock_calls) == 3

    # until the plan is complete, then the whole directory is skipped
    plan.operations[1].directory_statuses[subdir] = "completed"
    plan.run()
    assert len(mock_subprocess.mock_calls) == 3


def test_notimplemented_is_handled(subdir, monkeypatch):
    plan = Plan(
        operations=[RawCommand(config=RawCommand.OpConfig(arguments=["echo", "ok"]))],
        directories=[subdir],
    )
    m = MagicMock()
    m.side_effect = NotImplementedError
    monkeypatch.setattr("potent.operations.raw_command.RawCommand.run", m)

    plan.run()
    assert plan.directory_failed(subdir)


def test_read_data(subdir):
    plan = Plan(
        operations=[],
        directories=[subdir],
        data={str(subdir): {"cool": True, "age": 100, "name": "bruce"}},
    )
    assert plan.read_data(subdir, "cool")
    assert plan.read_data(subdir, "age") == 100
    assert plan.read_data(subdir, "name") == "bruce"


def test_data_serialization(subdir):
    plan = Plan(
        operations=[],
        directories=[subdir],
        data={str(subdir): {"cool": True, "age": 100, "name": "bruce"}},
    )
    json_str = plan.model_dump_json(exclude_none=True)
    parsed = json.loads(json_str)

    assert parsed["data"][str(subdir)]["cool"]
    assert parsed["data"][str(subdir)]["age"] == 100
    assert parsed["data"][str(subdir)]["name"] == "bruce"

    Plan.model_validate_json(json_str)
    assert plan.read_data(subdir, "cool")
    assert plan.read_data(subdir, "age") == 100
    assert plan.read_data(subdir, "name") == "bruce"


def test_read_data_error(subdir):
    plan = Plan(operations=[], directories=[subdir])

    with pytest.raises(DataReadException):
        plan.read_data(subdir, "name")

    plan = Plan(operations=[], directories=[subdir], data={})
    with pytest.raises(DataReadException):
        plan.read_data(subdir, "name")

    plan = Plan(operations=[], directories=[subdir], data={str(subdir): {}})
    with pytest.raises(DataReadException):
        plan.read_data(subdir, "name")


def test_write_data(subdir):
    plan = Plan(operations=[], directories=[subdir])
    plan.write_data(subdir, "cool", True)
    plan.write_data(subdir, "age", 100)
    plan.write_data(subdir, "name", "bruce")

    assert plan.data
    assert plan.data[str(subdir)] == {"cool": True, "age": 100, "name": "bruce"}


def test_status_no_data(subdir):
    plan = Plan(
        operations=[GitSwitch(config=GitSwitch.OpConfig(branch="{{name}}"))],
        directories=[subdir],
    )
    assert plan.status() == PlanStatus(
        filename=":in memory:",
        directories=[
            DirectoryStatus(
                path=subdir,
                status="not-started",
                op_results=[
                    OperationStatus(
                        status="not-started",
                        op_slug="git-switch",
                        # not resolved, which is fine
                        details="git switch -> {{ name }}",
                        completed_this_run=False,
                    )
                ],
            )
        ],
    )


def test_decsribe_no_data():
    p = Plan(
        directories=[],
        operations=[
            RawCommand(config=RawCommand.OpConfig(arguments=["echo", "{{name}}"]))
        ],
    )
    ops = p.outline().children[0].children

    # `describe` doesn't resolve, and that's fine
    assert "{{name}}" in ops[0].label  # pyright: ignore[reportOperatorIssue]


def test_templates_cant_run():
    with pytest.raises(ValueError):
        Plan(config=TemplateConfig(), directories=[], operations=[]).run()


def test_template_copying(tmp_path, monkeypatch: pytest.MonkeyPatch, subdir):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    template_plan = Plan(
        config=TemplateConfig(), operations=[GitStatus()], directories=[subdir]
    )
    template_path = tmp_path / "example.plan.json"
    template_plan.save(template_path)

    template_plan.convert_template()

    template_runs_dir = get_template_runs_dir()
    template_runs = list(template_runs_dir.iterdir())
    assert len(template_runs) == 1
    assert str(date.today()) in str(template_runs[0])


def test_rerunning_templates_dont_overwrite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, subdir
):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    template_plan = Plan(
        config=TemplateConfig(), operations=[GitStatus()], directories=[subdir]
    )
    template_path = tmp_path / "example.plan.json"
    template_plan.save(template_path)

    copied_plan = template_plan.convert_template()
    copied_plan.operations[0].record_result(subdir, True)
    copied_plan.save()
    assert copied_plan._path

    # this should _not_ overwrite the existing copy
    template_plan.convert_template()

    updated_template = Plan.from_path(copied_plan._path)

    # as a result, the directory is still complete
    assert updated_template.directory_complete(subdir)


def test_template_divergence_is_an_error(
    tmp_path, monkeypatch: pytest.MonkeyPatch, subdir
):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    template_plan = Plan(
        config=TemplateConfig(),
        operations=[GitSwitch(config=GitSwitch.OpConfig(branch="neat"))],
        directories=[subdir],
    )
    template_path = tmp_path / "example.plan.json"
    template_plan.save(template_path)

    copied_plan = template_plan.convert_template()
    copied_plan.operations[0].config.branch = "cool"  # type:ignore
    copied_plan.save()
    assert template_plan._path != copied_plan._path
    assert (
        template_plan.operations[0].config.branch  # type: ignore
        != copied_plan.operations[0].config.branch  # type: ignore
    )

    with pytest.raises(ValueError):
        template_plan.convert_template()


@pytest.mark.parametrize("num_files", [0, 1, 5, 15, 30])
def test_old_template_runs_are_cleared(
    tmp_path, monkeypatch: pytest.MonkeyPatch, num_files: int
):
    global_dir = tmp_path / "global"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))

    template_plan = Plan(config=TemplateConfig(), operations=[], directories=[])
    template_path = tmp_path / "example.plan.json"
    template_plan.save(template_path)
    stem = escape_path(template_path)

    runs_dir = get_template_runs_dir()
    runs_dir.mkdir(parents=True, exist_ok=True)
    assert len(list(runs_dir.iterdir())) == 0

    today = date.today()
    for days_ago in range(num_files):
        (runs_dir / f"{today - timedelta(days=days_ago)}_{stem}").touch()
    assert len(list(runs_dir.iterdir())) == num_files

    template_plan.clean_old_template_runs()

    assert len(list(runs_dir.iterdir())) == min(num_files, NUM_OLD_TEMPLATE_RUNS_KEPT)
    if num_files:
        assert (runs_dir / f"{today}_{stem}").exists()
