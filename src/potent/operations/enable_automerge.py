from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class Config(BaseConfig):
    mode: Literal["merge", "squash"] = "squash"
    """
    Sets the merge strategy for the PR.
    """


class EnableAutomerge(BaseOperation):
    """
    Enables auto-merge for the PR corresponding to the current branch.

    > [!IMPORTANT]
    > Requires the `gh` CLI to be installed.
    """

    slug: Literal["enable-automerge"]
    config: Config = Config()

    @override
    def _run(self, directory: Path) -> OperationResult:
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

        return OperationResult.from_process(result)
