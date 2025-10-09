import subprocess
from pathlib import Path
from typing import Literal

from shellprints.directives._base import BaseDirective


class GitPull(BaseDirective):
    slug: Literal["git-pull"]

    def _run(self, directory: Path) -> bool:
        result = subprocess.run(
            ["git", "pull"],
            cwd=directory,
            check=False,
            # capture_output=False,
        )

        if result.returncode == 0:
            return True

        # print(result.stderr)
        return False
