from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseDirective, DirectiveResult


class GitPush(BaseDirective):
    """
    Push to the remote repository.
    """

    slug: Literal["git-push"]

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(directory, ["git", "push"])

        return DirectiveResult.from_process(result, cmd=["git", "push"])
