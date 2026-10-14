from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseOperation, OperationResult


class GitPush(BaseOperation):
    """
    Push to the remote repository.
    """

    slug: Literal["git-push"] = "git-push"

    @override
    def run(self, directory: Path) -> OperationResult:
        return self.exec_cmd_with_result(directory, ["git", "push"])
