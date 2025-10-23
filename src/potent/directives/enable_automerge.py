from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


class Config(BaseConfig):
    mode: Literal["merge", "squash"] = "squash"
    """
    Sets the merge strategy for the PR.
    """


class EnableAutomerge(BaseDirective):
    """
    Enables automerge for the PR corresponding to the current branch.
    """

    slug: Literal["enable-automerge"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(
            directory,
            [
                "gh",
                "pr",
                "merge",
                "--auto",
                "--merge" if self.config.mode == "merge" else "squash",
            ],
        )

        return DirectiveResult.from_process(result)
