from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseOperation, OperationResult


class GitStatus(BaseOperation):
    """
    Ensures that you have a clean working directory. If there are any modified or unstaged files, this step fails.
    """

    slug: Literal["git-status"]

    @override
    def _run(self, directory: Path) -> OperationResult:
        cmd = ["git", "status", "--porcelain"]
        result = self._run_cmd(directory, cmd)

        success = not result.stdout

        return OperationResult(
            success=success,
            output="Working directory clean!" if success else result.stdout,
            cmd=" ".join(cmd),
        )
