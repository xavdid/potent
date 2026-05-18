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
def test_complex_skips_and_continues(mock_run: MagicMock, tmp_path, subdirs):
    # TODO: this test is a smelly code smell;
    # I need to do way too much setup to actually exec a plan
    plan_path = tmp_path / "example.plan.json"
    p = Plan(
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
    plan_path.write_text(p.model_dump_json())

    with Plan.open(plan_path) as plan:
        result = plan.run(Console(), plan_path)

    expected = RunSummary(
        filename="example.plan.json",
        directories=[
            DirectorySummary(
                name=subdirs[0],
                status="completed",
                op_results=[],
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
                    OperationSummary(status="completed", details=GitStatus().summary),
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

    assert json.loads(result.model_dump_json()) == json.loads(
        expected.model_dump_json()
    )
    # assert Plan(
    #     operations=[
    #         GitStatus(
    #             directory_statuses={
    #                 subdirs[0]: "completed",
    #                 subdirs[1]: "completed",
    #                 subdirs[2]: "failed",
    #             }
    #         ),
    #         GitStatus(
    #             directory_statuses={
    #                 subdirs[0]: "completed",
    #                 subdirs[1]: "failed",
    #             }
    #         ),
    #     ],
    #     directories=subdirs,
    # ).status(
    #     tmp_path,
    #     verbose_success_dirs=[subdirs[3]],
    #     just_completed_steps=[(1, subdirs[3])],
    # ) == PlanStatus(
    #     filename=str(tmp_path.absolute()),
    #     directories=[
    #         DirectoryStatus(
    #             name=subdirs[0],
    #             status="not-started",
    #             op_results=[
    #                 OperationResult(status="not-started", details=GitStatus().summary)
    #             ],
    #         ),
    #         DirectoryStatus(
    #             name=subdirs[1],
    #             status="completed",
    #             op_results=[],
    #         ),
    #         DirectoryStatus(
    #             name=subdirs[2],
    #             status="not-started",
    #             op_results=[],
    #         ),
    #         DirectoryStatus(
    #             name=subdirs[3],
    #             status="completed",
    #             op_results=[
    #                 OperationResult(status="completed", details=GitStatus().summary)
    #             ],
    #             completed_this_run=True,
    #         ),
    #     ],
    # )
