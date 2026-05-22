from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseOperation, OperationResult


class ManualConfirmation(BaseOperation):
    """
    A step that always fails. To advance your plan, manually edit the plan file so each directory succeeds.

    Useful for putting pauses into a multi-phase plan.
    """

    slug: Literal["manual-confirmation"] = "manual-confirmation"

    @override
    def _run(self, directory: Path) -> OperationResult:
        return OperationResult(
            success=False,
            output=f'Manually mark this step as completed for "{directory}" to proceed.',
        )

    @property
    @override
    def summary(self) -> str:
        if self.comment:
            return f"Halting because: {self.comment} (manual-confirmation)"
        # children will provide this if needed
        return self.slug  # type: ignore
