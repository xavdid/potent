from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional


@dataclass
class DirectoryStartedEvent:
    path: Path


@dataclass
class DirectorySkippedEvent:
    path: Path


@dataclass
class OperationCompletedEvent:
    path: Path
    summary: str
    result: Literal["success", "failure", "skipped"]
    output: str
    cmd: Optional[str] = None


RunEvent = DirectoryStartedEvent | DirectorySkippedEvent | OperationCompletedEvent
