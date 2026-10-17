from typing import Literal, Optional, override

from potent.operations._base import BaseConfig, BaseOperation, Context, OperationResult


class RawCommand(BaseOperation):
    """
    Runs a shell command. The step succeeds if the command exits 0 and fails otherwise. Useful for operations that potent doesn't support natively.
    """

    class OpConfig(BaseConfig):
        arguments: list[str]
        """
        The arguments that will be passed into Python's [subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run)
        """
        name: Optional[str] = None
        """
        A name used to disambiguate this step in summaries. Useful if you have many `raw-command`s.
        """
        write_output_to_key: Optional[str] = None
        """
        If specified, save a trimmed copy of the output to the `data` property under this key. Will save _all_ output, so only use when output is short.
        """

    slug: Literal["raw-command"] = "raw-command"
    config: OpConfig

    @override
    def run(self, context: Context) -> OperationResult:
        result = context.exec_raw_cmd(self.config.arguments)

        if key := self.config.write_output_to_key:
            context.write_data(key, result.stdout.strip())

        return OperationResult.from_process(result)

    @property
    @override
    def summary(self) -> str:
        if self.config.name:
            return f"{self.config.name} ({self.slug})"

        # truncate arguments larger than this in the summary
        LIMIT = 5

        segments = self.config.arguments[:LIMIT]
        msg = " ".join(f'"{s}"' if " " in s else s for s in segments)
        if len(self.config.arguments) > LIMIT:
            msg += "..."

        return f"{msg} ({self.slug})"
