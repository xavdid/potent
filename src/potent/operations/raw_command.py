from pathlib import Path
from typing import Literal, Optional, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class Config(BaseConfig):
    arguments: list[str]
    """
    The arguments that will be passed into Python's [subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run)
    """
    name: Optional[str] = None
    """
    A name used to disambiguate this step in summaries. Useful if you have many `raw-command`s.
    """


class RawCommand(BaseOperation):
    """
    Runs a shell command. The step succeeds if the command exits 0 and fails otherwise.
    """

    slug: Literal["raw-command"] = "raw-command"
    config: Config

    @override
    def _run(self, directory: Path) -> OperationResult:
        result = self._run_cmd(directory, self.config.arguments)

        return OperationResult.from_process(result, cmd=self.config.arguments)

    @property
    @override
    def name(self) -> str:
        if self.config.name:
            return f"{self.config.name} ({self.slug})"

        return super().name
