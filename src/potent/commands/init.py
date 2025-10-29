from pathlib import Path
from typing import Annotated

import typer

from potent.commands._types import is_plan_json
from potent.plan import Plan

app = typer.Typer()


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(
            exists=False,
            dir_okay=False,
            resolve_path=True,
            callback=is_plan_json,
            help="The location in which to write a new `.plan.json` file",
        ),
    ],
):
    """
    Create an empty plan at the specified path.
    """
    path.write_text(
        Plan(version="v1", steps=[], directories=[]).model_dump_json(indent=2)
    )
