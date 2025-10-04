import subprocess
from pathlib import Path
from typing import Literal, override

from shellprints.directives._base import BaseDirective


class CleanStatus(BaseDirective):
    slug: Literal["clean-status"]

    @override
    def run(self, directory: Path) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
        return not result.stdout
