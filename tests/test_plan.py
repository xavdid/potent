import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from potent.operations.git_status import GitStatus
from potent.plan import DirectorySummary, OperationSummary, Plan, RunSummary


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


def test_reset(tmp_path: Path):
    p = Plan(
        operations=[GitStatus(directory_statuses={tmp_path: "failed"})],
        directories=[tmp_path],
    )

    assert p.directory_failed(tmp_path)

    p.reset()

    assert p.directory_pending(tmp_path)


def test_only_first_pending_dir_prints_steps(tmp_path, subdirs):
    assert Plan(operations=[GitStatus()], directories=subdirs).status(
        tmp_path
    ) == RunSummary(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="not-started",
                op_results=[
                    OperationSummary(status="not-started", details=GitStatus().summary)
                ],
            ),
            *[
                DirectorySummary(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )


def test_success_doesnt_stop_print(tmp_path, subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses={subdirs[0]: "completed"})],
        directories=subdirs,
    )

    assert p.status(tmp_path) == RunSummary(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="completed",
                op_results=[],
            ),
            DirectorySummary(
                name=subdirs[1],
                status="not-started",
                op_results=[
                    OperationSummary(status="not-started", details=GitStatus().summary)
                ],
            ),
            *[
                DirectorySummary(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[2:]
            ],
        ],
    )


def test_failure_always_prints(tmp_path, subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses=dict.fromkeys(subdirs, "failed"))],
        directories=subdirs,
    )

    assert p.status(tmp_path) == RunSummary(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectorySummary(
                name=d,
                status="failed",
                op_results=[
                    OperationSummary(status="failed", details=GitStatus().summary)
                ],
            )
            for d in subdirs
        ],
    )


def test_failure_stops_prints(tmp_path, subdirs):
    p = Plan(
        operations=[GitStatus(directory_statuses={subdirs[0]: "failed"})],
        directories=subdirs,
    )

    assert p.status(tmp_path) == RunSummary(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="failed",
                op_results=[
                    OperationSummary(status="failed", details=GitStatus().summary)
                ],
            ),
            *[
                DirectorySummary(
                    name=d,
                    status="not-started",
                    op_results=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )


def test_completed_dirs_always_shown(tmp_path, subdirs):
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
        tmp_path,
        verbose_success_dirs=[subdirs[3]],
        just_completed_steps=[(1, subdirs[3])],
    ) == RunSummary(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="not-started",
                op_results=[
                    OperationSummary(status="not-started", details=GitStatus().summary)
                ],
            ),
            DirectorySummary(
                name=subdirs[1],
                status="completed",
                op_results=[],
            ),
            DirectorySummary(
                name=subdirs[2],
                status="not-started",
                op_results=[],
            ),
            DirectorySummary(
                name=subdirs[3],
                status="completed",
                op_results=[
                    OperationSummary(status="completed", details=GitStatus().summary)
                ],
                completed_this_run=True,
            ),
        ],
    )


@patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0))
def test_complex_skips_and_continues(_mock_run: MagicMock, tmp_path, subdirs):
    # TODO: this test is a smelly code smell;
    # I need to do way too much setup to actually exec a plan
    plan_path = tmp_path / "example.plan.json"
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
    result = plan.run(plan_path)

    expected = RunSummary(
        filename="example.plan.json",
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="completed",
                op_results=[],
                completed_this_run=False,
            ),
            DirectorySummary(
                name=subdirs[1],
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=False,
                    ),
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectorySummary(
                name=subdirs[2],
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=False,
                    ),
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectorySummary(
                name=subdirs[3],
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                    OperationSummary(
                        status="completed",
                        details=GitStatus().summary,
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
        ],
    )

    assert result == expected


def test_edge_cases(tmp_path):
    p = {
        "config": {"mode": "command", "last_run": "2026-05-17"},
        "version": "v1",
        "operations": [
            {
                "comment": "say where you're at",
                "directory_statuses": {
                    "~/projects/potent-demo/aardvark": "completed",
                    "~/projects/potent-demo/badger": "completed",
                    "~/projects/potent-demo/camel": "failed",
                },
                "slug": "raw-command",
                "config": {
                    "arguments": ["pwd"],
                },
            },
            {
                "comment": "say where you're at 2",
                "directory_statuses": {
                    "~/projects/potent-demo/aardvark": "completed",
                    "~/projects/potent-demo/badger": "failed",
                },
                "slug": "raw-command",
                "config": {
                    "arguments": ["pwd"],
                },
            },
        ],
        "directories": [
            "~/projects/potent-demo/aardvark",
            "~/projects/potent-demo/dingo",
            "~/projects/potent-demo/badger",
            "~/projects/potent-demo/camel",
        ],
    }
    plan = Plan(**p)
    path = tmp_path / "example.plan.json"
    results = plan.run(path)

    expected = RunSummary(
        filename=path,
        directories=[
            DirectorySummary(
                name=Path("~/projects/potent-demo/aardvark"),
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=False,
                    ),
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=False,
                    ),
                ],
                completed_this_run=False,
            ),
            DirectorySummary(
                name=Path("~/projects/potent-demo/dingo"),
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=True,
                    ),
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectorySummary(
                name=Path("~/projects/potent-demo/badger"),
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=False,
                    ),
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
            DirectorySummary(
                name=Path("~/projects/potent-demo/camel"),
                status="completed",
                op_results=[
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=False,
                    ),
                    OperationSummary(
                        status="completed",
                        details="pwd (raw-command)",
                        completed_this_run=True,
                    ),
                ],
                completed_this_run=True,
            ),
        ],
    )

    assert results == expected
