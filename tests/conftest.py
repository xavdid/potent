import importlib
import sys
from pathlib import Path

import pytest

from potent.operations._base import BaseOperation


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
