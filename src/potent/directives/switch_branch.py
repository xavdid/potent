from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


class Config(BaseConfig):
    branch: str
    """
    branch name
    """
    create_if_missing: bool = False
    """
    If true, tries creating the branch if switching to it fails
    """


class SwitchBranch(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["switch-branch"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        switch_without_create = self._run_cmd(
            directory,
            [
                "git",
                "switch",
                self.config.branch,
            ],
        )

        if (
            switch_without_create.returncode > 0
            and self.config.create_if_missing
            and "invalid reference" in switch_without_create.stdout
        ):
            return DirectiveResult.from_process(
                self._run_cmd(
                    directory,
                    [
                        "git",
                        "switch",
                        "-c",
                        self.config.branch,
                    ],
                )
            )

        return DirectiveResult.from_process(switch_without_create)
