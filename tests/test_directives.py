from pathlib import Path

import pytest

from potent.directives._base import BaseDirective


@pytest.mark.skip("errors aren't caught")
def test_directive_saves_on_fail(tmp_path: Path):
    b = BaseDirective(directory_statuses={tmp_path: "not-started"})

    assert not b.completed(tmp_path)
    assert not b.failed(tmp_path)

    b.run(tmp_path)

    assert b.failed(tmp_path)
