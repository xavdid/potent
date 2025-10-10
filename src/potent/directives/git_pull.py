import subprocess
from pathlib import Path
from typing import Literal

from potent.directives._base import BaseDirective, DirectiveResult


class GitPull(BaseDirective):
    slug: Literal["git-pull"]

    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(directory, ["git", "pull"])

        # print stdout? not sure if/when it's useful, can be long
        return DirectiveResult.from_process(result)

        if result.returncode == 0:
            return True

        # print(result.stderr)
        return False
