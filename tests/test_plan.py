from pathlib import Path

import pytest

from potent.operations.git_status import GitStatus
from potent.plan import DirectoryStatus, OperationResult, Plan, PlanStatus


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
    ) == PlanStatus(
        filename=str(tmp_path.absolute()),
        directories=[
            DirectoryStatus(
                name=subdirs[0],
                status="not-started",
                operations=[
                    OperationResult(status="not-started", details=GitStatus().summary)
                ],
            ),
            *[
                DirectoryStatus(
                    name=d,
                    status="not-started",
                    operations=[],
                )
                for d in subdirs[1:]
            ],
        ],
    )
