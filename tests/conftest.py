from pathlib import Path

import pytest


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
