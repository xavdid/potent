from pathlib import Path
from typing import Literal, override

from potent.operations._base import BaseConfig, BaseOperation, OperationResult


class Config(BaseConfig):
    arguments: list[str]
    """
    The arguments that will be passed into Python's [subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run)
    """


class RawCommand(BaseOperation):
    """
    Runs a shell command. The step succeeds if the command exits 0 and fails otherwise.
    """

    slug: Literal["raw-command"]
    config: Config

    @override
    def _run(self, directory: Path) -> OperationResult:
        result = self._run_cmd(directory, self.config.arguments)

        return OperationResult.from_process(result, cmd=self.config.arguments)
