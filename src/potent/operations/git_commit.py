from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class GitCommit(BaseOperation):
    """
    Commits staged files in git.
    """

    class OpConfig(BaseConfig):
        message: str
        """
        Commit message, submitted as is.
        """
        allow_empty: bool = False
        """
        If true, allows commits without changed/added files.
        """

    slug: Literal["git-commit"] = "git-commit"
    config: OpConfig

    @property
    @override
    def summary(self) -> str:
        LIMIT = 10
        msg = (
            f"{self.config.message[:LIMIT]}..."
            if len(self.config.message) > LIMIT
            else self.config.message
        )

        return f'git commit -m "{msg}"'

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
