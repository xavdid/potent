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
    The classic experience - command output is presented in its entirety
    """

    def __init__(self) -> None:
        self.console = Console()

    def send(self, event: RunEvent):
        match event:
            case DirectoryStarted(directory):
                self.console.rule(
                    f"📂 [bold underline]{directory.name}[/] 📂", style="bright_cyan"
                )
                self.console.print()
            case DirectorySkipped():
                self.console.print("☑️ [green]already finished")
            case OperationCompleted(
                summary=summary, result=result, output=output, cmd=cmd
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
