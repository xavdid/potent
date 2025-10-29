from pathlib import Path
from typing import Annotated

import typer


def is_plan_json(_ctx: typer.Context, _param: typer.CallbackParam, value: Path):
    if value.suffixes != [".plan", ".json"]:
        raise typer.BadParameter("File must have .plan.json extension")
    return value


# important that this _doesn't_ have a `type PlainJson =` declaration
PlanJson = Annotated[
    Path,
    typer.Argument(
        exists=True,
        dir_okay=False,
        resolve_path=True,
        callback=is_plan_json,
        help="The location of a `.plan.json` file",
    ),
]
