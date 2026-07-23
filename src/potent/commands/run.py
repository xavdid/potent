from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from potent.commands._types import PlanJson
from potent.plan import Plan
from potent.renderers import BasicRenderer

app = App()


@app.command()
def run(
    path: PlanJson,
    /,
    skip_reset: Annotated[
        bool,
        Parameter(
            negative="",
            help="If supplied, don't automatically reset a command plan. Ignored for non-command plans.",
        ),
    ] = False,
    skip_collapse: Annotated[
        bool,
        Parameter(
            negative="",
            help="If supplied, directories with identical results are repeated in full.",
        ),
    ] = False,
):
    """
    Execute a plan file and then print its status.
    """
    console = Console()

    console.print(f"Running [bold yellow]{str(path)}")

    plan = Plan.from_path(path)
    result = plan.run(
        skip_reset, renderer=BasicRenderer(), collapse_duplicates=not skip_collapse
    )

    console.print()
    console.rule("Summary")
    console.print(result.legend())
    console.print(result.to_tree())
