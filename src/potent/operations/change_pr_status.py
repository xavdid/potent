from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class ChangePrStatus(BaseOperation):
    """
    Change the readiness status of a PR. Moves it from draft -> "ready to review" by default, but can also move it back to draft.

    > [!IMPORTANT]
    > Requires the `gh` CLI to be installed.
    """

    class OpConfig(BaseConfig):
        to_status: Literal["ready", "draft"] = "ready"
        """
        Whether to mark the PR as ready or move it back to draft.
        """

    slug: Literal["change-pr-status"] = "change-pr-status"
    config: OpConfig = OpConfig()

    @property
    @override
    def summary(self) -> str:
        return f"Mark PR as {self.config.to_status}"

    @override
    def run(self, directory: Path) -> OperationResult:
        return self.exec_cmd_with_result(
            directory,
            [
                "gh",
                "pr",
                "ready",
                "--undo" if self.config.to_status == "draft" else "",
            ],
        )
