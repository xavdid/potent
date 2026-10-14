from typing import Literal, Self, override

from pydantic import model_validator

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class GitAdd(BaseOperation):
    """
    Stages files in git.
    """

    class OpConfig(BaseConfig):
        all: bool = False
        """
        If `true`, add stage files. Exactly one of `all` or `pattern` must be specified.
        """
        pattern: str = ""
        """
        The file(s) to stage. Is processed as a [Python glob](https://docs.python.org/3/library/glob.html). Exactly one of `all` or `pattern` must be specified.
        """

        @model_validator(mode="after")
        def check_something_to_add(self) -> Self:
            # exactly one of these should be truthy
            if self.all ^ bool(self.pattern):
                return self

            raise ValueError("set either `all` or `pattern`")

    slug: Literal["git-add"] = "git-add"
    config: OpConfig

    @property
    @override
    def summary(self) -> str:
        if self.config.all:
            suffix = " (all)"
        elif self.config.pattern:
            suffix = f" ({self.config.pattern})"
        else:
            suffix = ""  # can't reach this

        return f"git add{suffix}"

    @override
    def run(self, context: Context) -> OperationResult:
        if self.config.all:
            suffix = ["--all"]
        elif self.config.pattern:
            suffix = [str(s) for s in context.directory.glob(self.config.pattern)]
        else:
            raise RuntimeError("model validation should have prevented hitting this")

        return context.exec_cmd(["git", "add", *suffix])
