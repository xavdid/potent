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
):
    """
    Execute a plan file and then summarize it.
    """
    # TODO: probably make this internal to the class??
    # can maybe use a generator so the presentation is controlled in the CLI
    # update 2026-01-17; don't see a good way forward here. The plan is only occasionally invoked and most of the logic is presentational.
    console = Console()

    console.print(f"Running [bold yellow]{str(path)}")

    plan = Plan.from_path(path)
    result = plan.run(skip_reset, renderer=BasicRenderer())

    console.print()
    console.rule("Summary")
    console.print(result)
    console.print(result.to_tree())
