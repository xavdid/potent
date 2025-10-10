import typer

from potent.commands._types import PlanJson
from potent.shellprint import Shellprint

app = typer.Typer()


@app.command()
def reset(path: PlanJson):
    """
    Resets a plan file so it can be run again from scratch.
    """
    with path.open("r+") as plan_file:
        plan = Shellprint.from_file(plan_file)
        plan.reset()
        plan.save(plan_file)
