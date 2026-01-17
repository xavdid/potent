import subprocess
from pathlib import Path
from typing import Annotated, Literal, Optional, final, get_args

from pydantic import AfterValidator, BaseModel, ConfigDict, DirectoryPath, FilePath

from potent.util import format_annotation, table_row, truthy_list

Status = Literal["not-started", "failed", "completed"]


# useful for writing back absolute paths, which is good for portability
def make_abs_path(value: Path) -> Path:
    if not value.is_absolute():
        raise ValueError("path is not absolute")
    return value


AbsDirPath = Annotated[
    DirectoryPath,
    AfterValidator(make_abs_path),
]

AbsFilePath = Annotated[
    FilePath,
    AfterValidator(make_abs_path),
]
"""
AbsFilePath cool comment?
"""


class OperationResult(BaseModel):
    success: bool
    output: str
    cmd: Optional[str] = None

    @staticmethod
    def from_process(
        result: subprocess.CompletedProcess[str], cmd: Optional[list[str]] = None
    ):
        command = None

        if cmd:
            command = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)

        return OperationResult(
            success=result.returncode == 0, output=result.stdout, cmd=command
        )


class CommonBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaseConfig(CommonBase):
    model_config = ConfigDict(use_attribute_docstrings=True)


class BaseOperation(CommonBase):
    comment: Optional[str] = None
    directory_statuses: dict[AbsDirPath, Status] = {}

    @final
    def run(self, directory: Path) -> OperationResult:
        try:
            result = self._run(directory)
        # Could be anything, but I saw `FileNotFoundError` from subprocess.run when running non-existent commands
        except OSError as e:
            result = OperationResult(success=False, output=str(e))

        self.directory_statuses[directory] = "completed" if result.success else "failed"
        return result

    def _run(self, directory: Path) -> OperationResult:
        raise NotImplementedError

    def reset(self) -> None:
        self.directory_statuses = {}

    def completed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "completed"

    def failed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "failed"

    def pending(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory, "not-started") == "not-started"

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

    def _wrap_run(self, directory: Path, cmd: list[str]) -> OperationResult:
        result = self._run_cmd(directory, cmd)
        return OperationResult.from_process(result, cmd=cmd)

    @classmethod
    def to_markdown(cls) -> list[str]:
        """
        Returns a nicely formatted multiline markdown string that documents all of the properties on the model.
        """
        fields = cls.model_fields
        lines = [
            "",
            f"### {cls.__name__}",
            "",
            "\n".join(l.strip() for l in (cls.__doc__ or "").splitlines()),
            "",
            f"**Slug**: `{get_args(fields['slug'].annotation)[0]}`",
        ]

        if (raw_config := fields.get("config")) and raw_config.annotation:
            config = raw_config.annotation.model_fields

            lines += [
                "",
                f"#### Config{'' if raw_config.is_required() else ' (optional)'}",
                "",
                table_row(["name", "type", "description", "default (if optional)"]),
                table_row(["---"] * 4),
                *[
                    table_row(
                        [
                            f"`{conf_key}`",
                            format_annotation(v.annotation),
                            v.description,
                            ""
                            if v.is_required()
                            else f"`{f'"{v.default}"' if isinstance(v.default, str) else v.default}`",
                        ]
                    )
                    for conf_key, v in config.items()
                ],
            ]
        # return fields

        return lines
