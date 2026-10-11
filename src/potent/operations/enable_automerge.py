from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class SetAutomerge(BaseOperation):
    """
    Sets (or un-sets) auto-merge for the PR corresponding to the current branch.

    > [!IMPORTANT]
    > Requires the `gh` CLI to be installed.
    """

    class OpConfig(BaseConfig):
        enable: bool = True
        """
        Whether to set (or unset) auto-merge.
        """
        # these are fed right into the `gh` command, so they need to match the corresponding flags exactly
        # see: https://cli.github.com/manual/gh_pr_merge
        mode: Literal["merge", "squash"] = "squash"
        """
        Sets the merge strategy for the PR.
        """

    slug: Literal["set-automerge"] = "set-automerge"
    config: OpConfig = OpConfig()

    @override
    def run(self, directory: Path) -> OperationResult:
        return self.exec_cmd_with_result(
            directory,
            [
                "gh",
                "pr",
                "merge",
                f"--{'auto' if self.config.enable else 'disable-auto'}",
                f"--{self.config.mode}",
            ],
        )
