import rich
from cyclopts import App

from potent.commands._types import PlanJson
from potent.plan import Plan

app = App(name="describe")


@app.command()
def describe(path: PlanJson, /):
    """
    Print basic info about the plan, including the directories on which it acts and the steps involved.
    """

    rich.print(Plan.from_path(path).outline(path))
