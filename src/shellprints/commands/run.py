from time import sleep

import typer

from shellprints.commands._types import PlanJson
from shellprints.shellprint import Shellprint

app = typer.Typer()


@app.command()
def run(path: PlanJson):
    with path.open("r+") as plan_file:
        plan = Shellprint.model_validate_json(plan_file.read())
        plan.comment = f"{plan.comment or ''} cool"
        plan_file.seek(0)
        plan_file.truncate()
        plan_file.write(plan.model_dump_json(indent=2))
        plan_file.flush()

        sleep(2)
        plan.comment = ""
        plan_file.seek(0)
        plan_file.truncate()
        plan_file.write(plan.model_dump_json(indent=2))
        plan_file.flush()
