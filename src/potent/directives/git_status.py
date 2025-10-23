from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseDirective, DirectiveResult


class GitStatus(BaseDirective):
    """
    Ensures that you have a clean working directory. If there are any modified or unstaged files, this step fails.
    """

    slug: Literal["git-status"]

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        cmd = ["git", "status", "--porcelain"]
        result = self._run_cmd(directory, cmd)

        success = not result.stdout

        return DirectiveResult(
            success=success,
            output="Working directory clean!" if success else result.stdout,
            cmd=" ".join(cmd),
        )
