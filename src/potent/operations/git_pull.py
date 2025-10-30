from pathlib import Path
from typing import Literal

from potent.operations._base import BaseOperation, OperationResult


class GitPull(BaseOperation):
    """
    Pull from the remote repository.
    """

    slug: Literal["git-pull"]

    def _run(self, directory: Path) -> OperationResult:
        result = self._run_cmd(directory, ["git", "pull"])

        # print stdout? not sure if/when it's useful, can be long
        return OperationResult.from_process(result)
