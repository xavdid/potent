from pathlib import Path
from subprocess import CalledProcessError
from time import sleep

import typer
from rich.console import Console
from rich.panel import Panel

# from rich.live import Live
from shellprints.commands._types import PlanJson
from shellprints.shellprint import Shellprint

app = typer.Typer()


def directory_header(directory: Path) -> str:
    return f"📂 [bold underline]{directory.name}[not underline] 📂"


@app.command()
def run(path: PlanJson):
    # TODO: probably make this internal to the class??
    # can maybe use a generator so the presentation is controlled in the CLI
    plan = Shellprint.from_path(path)
    console = Console()

    console.print(f"Running [yellow]{str(path)}")

    with path.open("r+") as plan_file:
        for directory in plan.directories:
            console.print()
            if plan.directory_complete(directory):
                console.rule(directory_header(directory))
                # directory_spinner.ok(f"☑️ {directory.name}")
                console.print("☑️ [green]already finished")
                continue

            try:
                console.rule(directory_header(directory))

                for step in plan.steps:
                    console.print(
                        Panel(
                            "neat",
                            title=f"[dim]running step[not dim]: [underline]{step.slug}",
                            title_align="left",
                        )
                    )

                    console.print(
                        f"\n[dim]running step[not dim]: [underline]{step.slug}\n"
                    )
                    # with [].slug}") as task_spinner:
                    if step.completed(directory):
                        print("\n☑️ Already completed")
                        # task_spinner.ok("  ☑️ Skipping")
                        continue
                    success = step.run(directory)
                    plan.save(plan_file)
                    if success:
                        # plan.save(plan_file)
                        # task_spinner.ok("  OK")
                        console.print("✅ [green]Completed")
                    else:
                        # task_spinner.fail("  FAIL")
                        console.print("❌ [red]Failed")
                        break

            except (CalledProcessError, NotImplementedError):
                # directory_spinner.fail("ERR")
                print("    err!")
                continue
