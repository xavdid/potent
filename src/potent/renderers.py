from typing import Protocol, assert_never

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from potent.run_events import (
    DirectorySkipped,
    DirectoryStarted,
    OperationCompleted,
    RunEvent,
)


class Renderer(Protocol):
    """
    Renderers are responsible for printing the output of a Plan's run(). They mostly translate shell calls into readable and useful output.
    """

    def send(self, event: RunEvent): ...
    def log(self, msg: str): ...


class NoopRenderer:
    """
    This renderer intentionally does nothing; useful for tests and places where the pretty output of a run isn't used
    """

    def send(self, event: RunEvent):
        pass

    def log(self, msg: str):
        pass


class BasicRenderer:
    """
    The classic experience - command output is presented in its entirety.

    It's a little stateful, since it batches consecutive skipped steps in a given directory
    """

    def __init__(self) -> None:
        self.console = Console()
        self._reset_skipped_collection()

    def _reset_skipped_collection(self):
        self.skipped_steps: list[str] = []

    def send(self, event: RunEvent):
        match event:
            case DirectoryStarted(path):
                self.console.rule(
                    f"📂 [bold underline]{path.name}[/] 📂", style="bright_cyan"
                )
                self.console.print()
            case DirectorySkipped():
                self.console.print("☑️ [green]already finished")
            case OperationCompleted(
                summary=summary, result=result, output=output, cmd=cmd, path=path
            ):
                if result == "success":
                    subtitle = "Succeeded"
                    style = "green"
                elif result == "failure":
                    subtitle = "Failed"
                    style = "red"
                elif result == "skipped":
                    subtitle = "Skipped"
                    style = ""
                else:
                    assert_never(result)

                output = escape(output) or "[dim]no output[/]"
                if cmd:
                    output = f"[dim white]>>>[/] [cyan]{cmd}[/]\n\n{output}"

                if result == "skipped":
                    # if we're skipping something, it means the directory is worth running but we haven't gotten to the thing we're running yet
                    # so we can safely add to this list knowing it'll get cleared by by the first non-skipped item (the `else` below)
                    # i don't _think_ we need to track directories, since we'll always end a dir with an empty list.
                    self.skipped_steps.append(summary)
                else:
                    if self.skipped_steps:
                        # we've now hit a non-skip after hitting skips
                        # so, clear the queue and then print the thing that actually killed it
                        self.console.print(
                            Panel(
                                f"\n{'\n'.join(f'- {s}' for s in self.skipped_steps)}\n",
                                title_align="left",
                                subtitle="[dim white]result:[/] Skipped",
                                subtitle_align="left",
                            )
                        )
                        self.console.print()
                        self._reset_skipped_collection()

                    self.console.print(
                        Panel(
                            f"\n{output.strip()}\n",
                            title=f"[dim white]step[not dim]: {summary}",
                            title_align="left",
                            border_style=style,
                            subtitle=f"[dim white]result:[/] {subtitle}",
                            subtitle_align="left",
                        )
                    )
                    self.console.print()
            case other:
                assert_never(other)

    def log(self, msg: str):
        self.console.print(msg)
