from pathlib import Path

import pytest

from potent.commands._types import is_plan_json


@pytest.mark.parametrize(
    ["path", "success"], [[Path("cool"), False], [Path("cool.plan.json"), True]]
)
def test_is_plan_json(path: Path, success: bool):
    if success:
        assert is_plan_json(None, path) is None
    else:
        with pytest.raises(ValueError):
            is_plan_json(None, path)
