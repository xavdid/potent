import rich
import typer

from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


@app.command()
def info(path: PlanJson):
    """
    Print basic info about the plan, including the directories it acts on and the steps involved.
    """

    rich.print(Plan.from_path(path).outline(path))
