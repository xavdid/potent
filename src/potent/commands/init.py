from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter, validators
from cyclopts.types import NonExistentJsonPath

from potent.commands._types import is_plan_json, pathify
from potent.plan import Plan

app = App()


@app.command()
def init(
    path: Annotated[
        Path,
        Parameter(
            converter=pathify,
            validator=[
                is_plan_json,
                validators.Path(ext="json", file_okay=False, dir_okay=False),
            ],
            help="The location in which to to create a blank plan file. Can be a full path or a name. If a name, the named file must not exist in the configured command directory.",
        ),
    ],
    /,
):
    """
    Create an empty plan at the specified path.
    """

    path.write_text(
        Plan(version="v1", operations=[], directories=[]).model_dump_json(indent=2)
    )
