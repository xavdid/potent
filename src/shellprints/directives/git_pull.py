from pathlib import Path
from typing import Literal

from shellprints.directives._base import BaseDirective


class GitPull(BaseDirective):
    slug: Literal["git-pull"]

    def _run(self, directory: Path) -> bool:
        # TODO: fix
        if directory.name.endswith("haus"):
            return True

        return super().run(directory)
