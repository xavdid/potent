from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseDirective, DirectiveResult


class GitPush(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["git-push"]

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(directory, ["git", "push"])

        return DirectiveResult.from_process(result, cmd=["git", "push"])
