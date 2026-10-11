from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseOperation, OperationResult


class GitPull(BaseOperation):
    """
    Pull from the remote repository.
    """

    slug: Literal["git-pull"] = "git-pull"

    @override
    def run(self, directory: Path) -> OperationResult:
        # print stdout? not sure if/when it's useful, can be long
        return self.exec_cmd_with_result(directory, ["git", "pull"])
