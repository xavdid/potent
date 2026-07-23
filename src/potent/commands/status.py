from typing import Annotated

import rich
from cyclopts import App, Parameter

from potent.commands._types import PlanJson
from potent.plan import Plan

app = App()


@app.command()
def status(
    path: PlanJson,
    /,
    skip_collapse: Annotated[
        bool,
        Parameter(
            negative="",
            help="If supplied, directories with identical results are repeated in full.",
        ),
    ] = False,
):
    """
    Print the current state of a plan file, including the progress through each directory.
    """
    status = Plan.from_path(path).status(collapse_duplicates=not skip_collapse)
    rich.print(status.legend())
    rich.print(status.to_tree())
