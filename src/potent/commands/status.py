import rich
from cyclopts import App

from potent.commands._types import PlanJson
from potent.plan import Plan

app = App()


@app.command()
def status(path: PlanJson, /):
    """
    Print the current state of a plan file, including the progress through each directory.
    """
    rich.print(Plan.from_path(path).status(path))
