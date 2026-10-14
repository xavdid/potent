from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class GitSwitch(BaseOperation):
    """
    Switches the local git branch. Can optionally create it if it's missing.
    """

    class OpConfig(BaseConfig):
        branch: str
        """
        branch name
        """
        create_if_missing: bool = False
        """
        If true, tries creating the branch if switching to it fails
        """

    slug: Literal["git-switch"] = "git-switch"
    config: OpConfig

    @property
    @override
    def summary(self) -> str:
        return f"git switch -> {self.config.branch}"

    @override
    def run(self, context: Context) -> OperationResult:
        no_create_cmd = ["git", "switch", self.config.branch]
        switch_without_create = context.exec_raw_cmd(no_create_cmd)

        if (
            switch_without_create.returncode > 0
            and self.config.create_if_missing
            and "invalid reference" in switch_without_create.stdout
        ):
            cmd = ["git", "switch", "-c", self.config.branch]
            return OperationResult.from_process(context.exec_raw_cmd(cmd), cmd=cmd)

        return OperationResult.from_process(switch_without_create, cmd=no_create_cmd)
