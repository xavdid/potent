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
            dir_okay=False,
            resolve_path=True,
            callback=is_plan_json,
            help="The location in which to write a new `.plan.json` file. Must not exist",
        ),
    ],
):
    """
    Create an empty plan at the specified path.
    """
    if path.exists():
        raise ValueError(f"A file already exists at {path}")

    path.write_text(
        Plan(version="v1", operations=[], directories=[]).model_dump_json(indent=2)
    )
