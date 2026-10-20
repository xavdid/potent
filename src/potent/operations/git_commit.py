from typing import ClassVar, Literal, override

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class GitCommit(BaseOperation):
    """
    Commits staged files in git.
    """

    class OpConfig(BaseConfig):
        message: str
        """
        Commit message, submitted as is.
        """
        allow_empty: bool = False
        """
        If true, allows commits without changed/added files.
        """

        ignored_fields_for_compare: ClassVar[set[str]] = {"message"}

    slug: Literal["git-commit"] = "git-commit"
    config: OpConfig

    @property
    @override
    def summary(self) -> str:
        LIMIT = 15
        msg = (
            f"{self.config.message[:LIMIT]}..."
            if len(self.config.message) > LIMIT
            else self.config.message
        )

        return f'git commit -m "{msg}"'

    @override
    def run(self, context: Context) -> OperationResult:
        return context.exec_cmd(
            [
                "git",
                "commit",
                "-m",
                self.config.message,
                "--allow-empty" if self.config.allow_empty else "",
            ]
        )
