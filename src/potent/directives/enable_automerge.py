from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


class Config(BaseConfig):
    mode: Literal["merge", "squash"] = "squash"


class EnableAutomerge(BaseDirective):
    """
    Creates
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
