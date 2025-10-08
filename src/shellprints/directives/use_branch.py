import subprocess
from pathlib import Path
from typing import Literal, Optional, override

from shellprints.directives._base import BaseDirective


class UseBranch(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["create-branch"]
    branch: str
    """
    branch name
    """
    # base: Optional[str]
    # """
    # Branch to base the new branch off of. Will switch to this first to create the branch.
    # """

    @override
    def _run(self, directory: Path) -> bool:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
