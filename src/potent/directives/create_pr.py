from pathlib import Path
from typing import Literal, Optional, Self, override

from pydantic import ConfigDict, FilePath, model_validator

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


# remove if unused:
class Config(BaseConfig):
    title: str

    body_text: Optional[str] = None
    body_file: Optional[FilePath] = None

    draft: bool = False
    base_branch: Optional[str] = None

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if not (self.body_text or self.body_file):
            raise ValueError("Need one of `body_text` or `body_file`")
        return self


class CreatePR(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["create-pr"]
    config: Config
    model_config = ConfigDict(extra="forbid")

    @override
    def _run(self, directory: Path) -> DirectiveResult:
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

        return DirectiveResult.from_process(result)
