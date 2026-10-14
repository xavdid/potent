from typing import Literal, override

from potent.operations._base import BaseOperation, Context, OperationResult


class GitStatus(BaseOperation):
    """
    Ensures that you have a clean working directory. If there are any modified or un-staged files, this step fails.
    """

    slug: Literal["git-status"] = "git-status"

    @override
    def run(self, context: Context) -> OperationResult:
        cmd = ["git", "status", "--porcelain"]
        result = context.exec_raw_cmd(cmd)

        success = not result.stdout

        return OperationResult(
            success=success,
            output="Working directory clean!" if success else result.stdout,
            cmd=" ".join(cmd),
        )
