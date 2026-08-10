from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from potent.commands._types import DisplayModeOptions, PlanJson
from potent.display_modes import CompactDisplayMode
from potent.plan import Plan
from potent.renderers import BasicRenderer

app = App()


@app.command()
def run(
    path: PlanJson,
    /,
    display_mode: DisplayModeOptions = CompactDisplayMode,
    skip_reset: Annotated[
        bool,
        Parameter(
            negative="",
            help="If supplied, don't automatically reset a command plan. Ignored for non-command plans.",
        ),
    ] = False,
):
    """
    Execute a plan file and then print its status.
    """
    console = Console()

    console.print(f"Running [bold yellow]{str(path)}")

    plan = Plan.from_path(path)
    completed_steps = plan.run(skip_reset, renderer=BasicRenderer(display_mode))

    result = plan.status(
        just_completed_steps=completed_steps,
        collapse_duplicates=not display_mode.show_duplicate_statuses,
    )

    console.print()
    console.rule("Summary")
    console.print(result.legend())
    console.print(result.to_tree())
