import subprocess
from pathlib import Path
from typing import Literal, Optional, override

from pydantic import BaseModel

from shellprints.directives._base import BaseDirective
from shellprints.util import indent_command_output, truthy_list


class Config(BaseModel):
    branch: str
    create: bool = False


class SwitchBranch(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["switch-branch"]
    config: Config
    """
    branch name
    """
    # base: Optional[str]
    # """
    # Branch to base the new branch off of. Will switch to this first to create the branch.
    # """

    @override
    def _run(self, directory: Path) -> bool:
        command = truthy_list(
            [
                "git",
                "switch",
                "-c" if self.config.create else "",
                self.config.branch,
            ]
        )
        # command = [
        #     "git",
        #     "switch",
        #     "-c" if self.config.create else "",
        #     self.config.branch,
        # ]

        result = subprocess.run(
            command, cwd=directory, check=False, capture_output=True
        )

        if result.returncode == 0:
            return True

        print(indent_command_output(result.stderr))
        return False

    def verify(self) -> None:
        """
        verify branch on every run
        """
