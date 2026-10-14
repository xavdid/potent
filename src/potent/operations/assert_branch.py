from typing import ClassVar, Literal, override

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class AssertBranch(BaseOperation):
    """
    Fails if the current git branch doesn't match the configured one. Useful for ensuring a plan is always run against the intended branch. Helpful if you've been working in a directory and want to be sure a plan only runs against a specific branch.

    > [!NOTE]
    > This operation will be executed on every run, not just until it succeeds.
    """

    class OpConfig(BaseConfig):
        branch: str
        """
        branch name
        """

    slug: Literal["assert-branch"] = "assert-branch"
    config: OpConfig

    always_rerun: ClassVar[bool] = True

    @property
    @override
    def summary(self) -> str:
        return f"assert branch == {self.config.branch}"

    @override
    def run(self, context: Context) -> OperationResult:
        cmd = ["git", "branch", "--show-current"]
        result = context.exec_raw_cmd(cmd)
        current_branch = result.stdout.strip()

        success = current_branch == self.config.branch
        output = (
            "Branch matches!"
            if success
            else f'Currently on branch "{current_branch}", expected "{self.config.branch}"'
        )

        return OperationResult(success=success, output=output, cmd=" ".join(cmd))
