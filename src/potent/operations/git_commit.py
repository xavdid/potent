from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class Config(BaseConfig):
    message: str
    """
    Commit message, submitted as is.
    """
    allow_empty: bool = False
    """
    If true, allows commits without changed/added files.
    """


class GitCommit(BaseOperation):
    """
    Commits staged files in git.
    """

    slug: Literal["git-commit"]
    config: Config

    @override
    def _run(self, directory: Path) -> OperationResult:
        cmd = [
            "git",
            "commit",
            "-m",
            self.config.message,
            "--allow-empty" if self.config.allow_empty else "",
        ]
        result = self._run_cmd(directory, cmd)

        return OperationResult.from_process(result, cmd=cmd)
