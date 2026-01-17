from pathlib import Path
from typing import Literal, Optional, Self, override

from pydantic import model_validator

from potent.operations._base import (
    AbsFilePath,
    BaseConfig,
    BaseOperation,
    OperationResult,
)


class Config(BaseConfig):
    title: str
    """
    The title of the PR.
    """

    body_text: Optional[str] = None
    """
    A string that will be used as the body of the PR. Exactly one of `body_text` or `body_file` is required.
    """
    body_file: Optional[AbsFilePath] = None
    """
    The absolute path to a readable file containing the full body of the PR. Exactly one of `body_text` or `body_file` is required.
    """

    draft: bool = False
    """
    Whether to open the PR in draft mode.
    """

    base_branch: Optional[str] = None
    """
    The branch that you want to merge your changes into. Defaults to the repo's default branch.
    """

    @model_validator(mode="after")
    def check_body_source(self) -> Self:
        if self.body_text and self.body_file:
            raise ValueError("Supply exactly one of `body_text` or `body_file`.")

        if not (self.body_text or self.body_file):
            raise ValueError("Need one of `body_text` or `body_file`")

        return self


class CreatePR(BaseOperation):
    """
    Creates a pull request using the `gh` CLI.

    > [!IMPORTANT]
    > Requires the `gh` CLI to be installed.
    """

    slug: Literal["create-pr"]
    config: Config

    @override
    def _run(self, directory: Path) -> OperationResult:
        cmd = ["gh", "pr", "create", "--title", self.config.title]

        if self.config.body_file:
            cmd += ["--body-file", str(self.config.body_file)]
        elif self.config.body_text:
            cmd += ["--body", self.config.body_text]
        else:
            raise RuntimeError("validation should have caught this")

        if self.config.draft:
            cmd.append("--draft")

        if self.config.base_branch:
            cmd += ["--base", self.config.base_branch]

        result = self._run_cmd(
            directory,
            cmd,
        )

        return OperationResult.from_process(result)
