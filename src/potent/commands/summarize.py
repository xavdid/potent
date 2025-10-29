import rich
import typer

from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


@app.command()
def summarize(path: PlanJson):
    """
    Summarize the current state of a plan file. Also validates the file for schema issues.
    """
    rich.print(Plan.from_path(path).summarize(path))
