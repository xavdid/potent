from pathlib import Path
from typing import Literal, override

from pydantic import BaseModel

from potent.directives._base import BaseDirective, DirectiveResult


# remove if unused:
class Config(BaseModel):
    message: str


class GitCommit(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["git-commit"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(
            directory,
            ["git", "commit", "-m", self.config.message],
        )

        return DirectiveResult.from_process(result)
