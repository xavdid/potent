import typer

from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


@app.command()
def reset(path: PlanJson):
    """
    Reset the progress on a plan file so it can be run again from scratch.
    """
    with path.open("r+") as plan_file:
        plan = Plan.from_file(plan_file)
        plan.reset()
        plan.save(plan_file)
