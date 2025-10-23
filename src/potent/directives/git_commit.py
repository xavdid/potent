from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


# remove if unused:
class Config(BaseConfig):
    message: str
    """
    Commit message, submitted as is.
    """
    allow_empty: bool = False
    """
    If true, allows commits without changed/added files.
    """


class GitCommit(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["git-commit"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        cmd = [
            "git",
            "commit",
            "-m",
            self.config.message,
            "--allow-empty" if self.config.allow_empty else "",
        ]
        result = self._run_cmd(directory, cmd)

        return DirectiveResult.from_process(result, cmd=cmd)
