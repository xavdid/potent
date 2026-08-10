import rich
from cyclopts import App

from potent.commands._types import DisplayModeOptions, PlanJson
from potent.display_modes import StandardDisplayMode
from potent.plan import Plan

app = App()


@app.command()
def status(
    path: PlanJson,
    /,
    display_mode: DisplayModeOptions = StandardDisplayMode,
):
    """
    Print the current state of a plan file, including the progress through each directory.
    """
    status = Plan.from_path(path).status(
        collapse_duplicates=not display_mode.show_duplicate_statuses
    )
    rich.print(status.legend())
    rich.print(status.to_tree())
