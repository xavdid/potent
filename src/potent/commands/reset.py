import typer

from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


@app.command()
def reset(path: PlanJson):
    """
    Reset the progress on a plan file so it can be run again from scratch.
    """
    with Plan.open(path) as plan:
        plan.reset()
        plan.save()
