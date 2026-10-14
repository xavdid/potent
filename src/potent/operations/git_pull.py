from typing import Literal, override

from potent.operations._base import BaseOperation, Context, OperationResult


class GitPull(BaseOperation):
    """
    Pull from the remote repository.
    """

    slug: Literal["git-pull"] = "git-pull"

    @override
    def run(self, context: Context) -> OperationResult:
        # print stdout? not sure if/when it's useful, can be long
        return context.exec_cmd(["git", "pull"])
