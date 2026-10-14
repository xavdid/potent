from typing import Literal, Optional, override

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class ManualConfirmation(BaseOperation):
    """
    A step that always fails. To advance your plan, manually edit the plan file so each directory succeeds.

    Useful for putting pauses into a multi-phase plan.
    """

    class OpConfig(BaseConfig):
        reason: Optional[str] = None
        """
        User-facing reason for the pause
        """

    slug: Literal["manual-confirmation"] = "manual-confirmation"
    config: OpConfig = OpConfig()

    @override
    def run(self, context: Context) -> OperationResult:
        return OperationResult(
            success=False,
            output=f'Manually mark this step as completed for "{context.directory}" to proceed.',
        )

    @property
    @override
    def summary(self) -> str:
        if self.config.reason:
            return f"{self.config.reason} (manual-confirmation)"

        return self.slug
