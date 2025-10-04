from pathlib import Path
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, DirectoryPath


# useful for writing back absolute paths, which is good for portability
def make_abs_path(value: Path) -> Path:
    if not value.is_absolute():
        raise ValueError("path is not absolute")
    return value


type AbsPathList = list[
    Annotated[
        DirectoryPath,
        AfterValidator(make_abs_path),
    ]
]


class BaseDirective(BaseModel):
    comment: Optional[str] = None
    completed_directories: AbsPathList = []

    def run(self, directory: Path) -> bool:
        raise NotImplementedError

    def reset(self) -> None:
        self.completed_directories = []
