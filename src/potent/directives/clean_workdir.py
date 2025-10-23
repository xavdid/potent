from pathlib import Path
from time import sleep
from typing import Literal, override

from potent.directives._base import BaseDirective, DirectiveResult


class CleanStatus(BaseDirective):
    """
    asdf
    """

    slug: Literal["clean-status"]

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
