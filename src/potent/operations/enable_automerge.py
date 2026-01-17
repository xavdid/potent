from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class Config(BaseConfig):
    # these are fed right into the `gh` command, so they need to match the corresponding flags exactly
    # see: https://cli.github.com/manual/gh_pr_merge
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
            ["gh", "pr", "merge", "--auto", f"--{self.config.mode}"],
        )

        return OperationResult.from_process(result)
