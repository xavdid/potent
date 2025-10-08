from pathlib import Path
from typing import Annotated, Literal, Optional, final

from pydantic import AfterValidator, BaseModel, DirectoryPath

Status = Literal["not-started", "failed", "completed"]


# useful for writing back absolute paths, which is good for portability
def make_abs_path(value: Path) -> Path:
    if not value.is_absolute():
        raise ValueError("path is not absolute")
    return value


AbsPath = Annotated[
    DirectoryPath,
    AfterValidator(make_abs_path),
]


class BaseDirective(BaseModel):
    comment: Optional[str] = None
    directory_statuses: dict[AbsPath, Status] = {}

    @final
    def run(self, directory: Path) -> bool:
        try:
            success = self._run(directory)
            self.directory_statuses[directory] = "completed" if success else "failed"

            return success
        except Exception:  # noqa: BLE001
            return False

    def _run(self, directory: Path) -> bool:
        raise NotImplementedError

    def reset(self) -> None:
        self.directory_statuses = {}

    def completed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "completed"

    def failed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "failed"

    def initialize_dirs(self, directories: list[Path]) -> None:
        self.directory_statuses |= dict.fromkeys(directories, "not-started")
