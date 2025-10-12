import subprocess
from pathlib import Path
from typing import Annotated, Literal, Optional, final

from pydantic import AfterValidator, BaseModel, DirectoryPath

from potent.util import truthy_list

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


class DirectiveResult(BaseModel):
    success: bool
    output: str
    cmd: Optional[str] = None

    @staticmethod
    def from_process(
        result: subprocess.CompletedProcess[str], cmd: Optional[list[str]] = None
    ):
        command = None

        if cmd:
            command = " ".join(cmd)

        return DirectiveResult(
            success=result.returncode == 0, output=result.stdout, cmd=command
        )


class BaseDirective(BaseModel):
    comment: Optional[str] = None
    directory_statuses: dict[AbsPath, Status] = {}

    @final
    def run(self, directory: Path) -> DirectiveResult:
        # try:
        result = self._run(directory)
        # except Exception:  # noqa: BLE001
        #     success = False

        self.directory_statuses[directory] = "completed" if result.success else "failed"
        return result

    def _run(self, directory: Path) -> DirectiveResult:
        raise NotImplementedError

    def reset(self) -> None:
        self.directory_statuses = {}

    def completed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "completed"

    def failed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "failed"

    def initialize_dirs(self, directories: list[Path]) -> None:
        self.directory_statuses |= dict.fromkeys(directories, "not-started")

    def _run_cmd(
        self, directory: Path, cmd: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """
        helper for shelling out
        """
        return subprocess.run(
            truthy_list(cmd),
            cwd=directory,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
