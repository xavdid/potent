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
            success=False, output="Manually edit the plan file to proceed"
        )
