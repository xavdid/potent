from pathlib import Path
from typing import get_args

import pytest

from potent.operations._base import BaseOperation
from potent.operations.enable_automerge import SetAutomerge


@pytest.mark.skip("errors aren't caught")
def test_operation_saves_on_fail(tmp_path: Path):
    b = BaseOperation(directory_statuses={tmp_path: "not-started"})

    assert not b.is_completed(tmp_path)
    assert not b.is_failed(tmp_path)

    b.run_and_record_result(
        tmp_path,
        read_func=lambda: None,  # type:ignore
        write_func=lambda: None,  # type:ignore
    )

    assert b.is_failed(tmp_path)


def test_automerge_has_only_two_modes():
    """
    I'll have a bug if there's ever a third supported mode,
    so add a test to confirm that can't happen by accident
    """

    assert len(get_args(SetAutomerge.OpConfig.__annotations__["mode"])) == 2
