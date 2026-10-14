import importlib
import re
import sys
from typing import Literal
from unittest.mock import MagicMock, patch

import pytest

from potent.operations._base import BaseOperation
from potent.plugins import get_ops_from_plugins, validate_plugin


@pytest.fixture
def define_plan_with_extra_ops(monkeypatch):
    """
    Fixture to patch the plugin loader and force a re-import of the plan.py file, which re-runs the class declaration
    """

    def _import(*ops: list[type[BaseOperation]]):
        monkeypatch.setattr("potent.plugins.get_ops_from_plugins", lambda: ops)
        # clear the module
        monkeypatch.delitem(sys.modules, "potent.plan", raising=False)
        # re-import so the patched value is used
        return importlib.import_module("potent.plan")

    yield _import

    # drop the throwaway module so later tests re-import the real one
    sys.modules.pop("potent.plan", None)


class CorrectOp(BaseOperation):
    slug: Literal["my-plugin.test-op"] = "my-plugin.test-op"


class SluglessOp(BaseOperation):
    pass


class SlugWithoutDefaultOp(BaseOperation):
    slug: Literal["my-plugin.test-op"]


class SlugWithoutPrefixOp(BaseOperation):
    slug: Literal["test-op"] = "test-op"


@pytest.mark.parametrize(
    ["entrypoint", "expected_err_patterns"],
    [
        # no ops is fine
        (MagicMock(load=MagicMock(return_value=[])), []),
        # need a list as the value
        (MagicMock(load=MagicMock(return_value={})), [r"must be lists.*my-plugin"]),
        # items must be children of BaseOperation
        (
            MagicMock(load=MagicMock(return_value=[int, CorrectOp, dict])),
            [
                r"my-plugin.my-ops:.*index 0.*BaseOperation",
                r"my-plugin.my-ops:.*index 2.*BaseOperation",
            ],
        ),
        # must have a slug
        (
            MagicMock(load=MagicMock(return_value=[SluglessOp])),
            [r"my-plugin.my-ops:.*no.*slug"],
        ),
        # slug must have a default
        (
            MagicMock(load=MagicMock(return_value=[SlugWithoutDefaultOp])),
            [r"my-plugin.my-ops:.*not.*default value"],
        ),
        # slug must have a prefix
        (
            MagicMock(load=MagicMock(return_value=[SlugWithoutPrefixOp])),
            [r'my-plugin.my-ops:.*start with.*"my-plugin\."'],
        ),
    ],
)
def test_plugin_validation(entrypoint, expected_err_patterns):
    # these need to be set outside constructor because `name` is a protected property name
    entrypoint.name = "my-ops"
    entrypoint.dist.name = "my-plugin"
    _, errors = validate_plugin(entrypoint)

    assert len(expected_err_patterns) == len(errors)
    for patt, err in zip(expected_err_patterns, errors):
        assert re.search(patt, err), f'"{patt}" not found in "{err}"'


def test_loading_ops(define_plan_with_extra_ops, subdir):
    class TestOp(BaseOperation):
        slug: Literal["test-op"] = "test-op"

    plan = define_plan_with_extra_ops(TestOp)

    plan.Plan(operations=[TestOp()], directories=[subdir])


@patch("potent.plugins.entry_points", return_value=[MagicMock(), MagicMock()])
def test_errors_are_batched(_, capsys):
    with pytest.raises(RuntimeError):
        get_ops_from_plugins()

    captured = capsys.readouterr()
    assert captured.out.count("must be lists") == 2


@patch("potent.plugins.entry_points")
def test_loads_all_plugins(mock_entry_points):
    p1 = MagicMock(load=lambda: [CorrectOp])
    p1.name = "my-ops"
    p1.dist.name = "my-plugin"

    p2 = MagicMock(load=lambda: [CorrectOp])
    p2.name = "my-other-ops"
    p2.dist.name = "my-plugin"

    mock_entry_points.return_value = [p1, p2]

    assert get_ops_from_plugins() == [CorrectOp, CorrectOp]
