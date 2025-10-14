from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

# from rich.live import Live
from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


def directory_header(console: Console, directory: Path) -> None:
    return console.rule(
        f"📂 [bold underline]{directory.name}[/] 📂", style="bright_cyan"
    )


@app.command()
def run(path: PlanJson):
    # TODO: probably make this internal to the class??
    # can maybe use a generator so the presentation is controlled in the CLI
    plan = Plan.from_path(path)
    console = Console()

    console.print(f"Running [bold yellow]{str(path)}")

    with path.open("r+") as plan_file:
        for directory in plan.directories:
            console.print()
            if plan.directory_complete(directory):
                directory_header(console, directory)

                # directory_spinner.ok(f"☑️ {directory.name}")
                console.print("☑️ [green]already finished")
                continue

            try:
                directory_header(console, directory)

                for step in plan.steps:
                    success = None
                    output = ""
                    style = ""
                    if step.completed(directory):
                        output = "Already completed"
                        subtitle = "skipped"
                    else:
                        result = step.run(directory)
                        plan.save(plan_file)
                        if success := result.success:
                            style = "green"
                            subtitle = "Succeeded"
                        else:
                            style = "red"
                            subtitle = "Failed"

                        output = result.output or "[dim]no output"
                        if result.cmd:
                            output = f"[dim white]ran:[/] `{result.cmd}`\n\n{output}"

                    console.print(
                        Panel(
                            f"\n{output.strip()}\n",
                            title=f"[dim white]step[not dim]: {step.slug}",
                            title_align="left",
                            border_style=style,
                            subtitle=f"[dim white]result:[/] {subtitle}",
                            subtitle_align="left",
                        )
                    )
                    console.print()
                    if success is False:
                        break

            except NotImplementedError:
                # directory_spinner.fail("ERR")
                print("    err!")
                continue

    console.print()
    console.rule("Summary")
    console.print(plan.summarize(path, short_plan=True))
