from pathlib import Path
from time import sleep
from typing import Literal, override

from potent.directives._base import BaseDirective, DirectiveResult


class CleanWorkdir(BaseDirective):
    slug: Literal["clean-status"]

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(directory, ["git", "status", "--porcelain"])
        sleep(2)

        success = not result.stdout

        return DirectiveResult(
            success=success,
            output="Working directory clean!"
            if success
            else "Uncommitted changes; clear before proceeding.",
        )
