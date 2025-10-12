from pathlib import Path
from typing import Literal, Self, override

from pydantic import BaseModel, model_validator

from potent.directives._base import BaseDirective, DirectiveResult


# remove if unused:
class Config(BaseModel):
    all: bool = False
    pattern: str = ""

    @model_validator(mode="after")
    def check_something_to_add(self) -> Self:
        # exactly one of these should be truthy
        if self.all ^ bool(self.pattern):
            return self

        raise ValueError("set either `all` or `patterns`")


class GitAdd(BaseDirective):
    """
    Creates a branch if missing. Re-verifies that you're on that branch during every run.
    """

    slug: Literal["git-add"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        if self.config.all:
            suffix = ["--all"]
        elif self.config.pattern:
            suffix = [str(s) for s in directory.glob(self.config.pattern)]
        else:
            raise RuntimeError("model validation should have prevented hitting this")

        cmd = ["git", "add", *suffix]
        result = self._run_cmd(
            directory,
            cmd,
        )

        return DirectiveResult.from_process(result, cmd=cmd)
