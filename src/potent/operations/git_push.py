from typing import Literal, override

from potent.operations._base import BaseOperation, Context, OperationResult


class GitPush(BaseOperation):
    """
    Push to the remote repository.
    """

    slug: Literal["git-push"] = "git-push"

    @override
    def run(self, context: Context) -> OperationResult:
        return context.exec_cmd(["git", "push"])
