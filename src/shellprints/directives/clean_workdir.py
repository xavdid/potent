import subprocess
from pathlib import Path
from time import sleep
from typing import Literal, override

from shellprints.directives._base import BaseDirective


class CleanWorkdir(BaseDirective):
    slug: Literal["clean-status"]

    @override
    def _run(self, directory: Path) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
        sleep(2)

        return not result.stdout
