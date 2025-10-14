from pathlib import Path
from typing import get_args

import pytest

from potent.directives._base import BaseDirective
from potent.directives.enable_automerge import Config as AutomergeConfig


@pytest.mark.skip("errors aren't caught")
def test_directive_saves_on_fail(tmp_path: Path):
    b = BaseDirective(directory_statuses={tmp_path: "not-started"})

    assert not b.completed(tmp_path)
    assert not b.failed(tmp_path)

    b.run(tmp_path)

    assert b.failed(tmp_path)


def test_automerge_has_only_two_modes():
    """
    I'll have a bug if there's ever a third supported mode,
    so add a test to confirm that can't happen by accident
    """

    assert len(get_args(AutomergeConfig.__annotations__["mode"])) == 2
