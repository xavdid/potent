"""
This file holds a Rust-style enum to communicate updates about the plan execution to a renderer.
It acts as a bridge between the computation layer and the presentational one.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional


@dataclass
class DirectoryStarted:
    path: Path


@dataclass
class DirectorySkipped:
    path: Path


@dataclass
class OperationCompleted:
    path: Path
    summary: str
    result: Literal["success", "failure", "skipped"]
    output: str
    cmd: Optional[str] = None


RunEvent = DirectoryStarted | DirectorySkipped | OperationCompleted
