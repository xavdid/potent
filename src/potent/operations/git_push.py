from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseOperation, OperationResult


class GitPush(BaseOperation):
    """
    Push to the remote repository.
    """

    slug: Literal["git-push"]

    @override
    def _run(self, directory: Path) -> OperationResult:
        result = self._run_cmd(directory, ["git", "push"])

        return OperationResult.from_process(result, cmd=["git", "push"])
