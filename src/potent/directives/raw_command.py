from pathlib import Path
from typing import Literal, override

from potent.directives._base import BaseConfig, BaseDirective, DirectiveResult


class Config(BaseConfig):
    arguments: list[str]
    """
    The arguments that will be passed into Python's [subprocess.run](https://docs.python.org/3/library/subprocess.html#subprocess.run)
    """


class RawCommand(BaseDirective):
    """
    Runs a bash command. The step is successful if it exits 0 and fails otherwise.
    """

    slug: Literal["raw-command"]
    config: Config

    @override
    def _run(self, directory: Path) -> DirectiveResult:
        result = self._run_cmd(directory, self.config.arguments)

        return DirectiveResult.from_process(result, cmd=self.config.arguments)
