from cyclopts import App
from rich.console import Console

from potent.commands._types import PlanJson
from potent.display_modes import DisplayModeFlag, StandardDisplayMode
from potent.plan import Plan
from potent.renderers import BasicRenderer, CompactRenderer

app = App()


@app.command()
def run(path: PlanJson, /, display_mode: DisplayModeFlag = StandardDisplayMode):
    """
    Execute a plan file and then print its status.
    """
    original_plan = Plan.from_path(path)

    if is_template := original_plan.config.mode == "template":
        plan = original_plan.convert_template()
    else:
        plan = original_plan

    console = Console()
    console.print(
        f"{'Copying template' if is_template else 'Running'} [bold yellow]{str(path)}"
    )

    completed_steps = plan.run(
        renderer=CompactRenderer()
        if display_mode.name == "quiet"
        else BasicRenderer(display_mode)
    )

    result = plan.status(
        just_completed_steps=completed_steps,
        collapse_duplicates=not display_mode.show_duplicate_statuses,
    )

    console.print()
    console.rule("Summary")
    console.print(result.legend())
    console.print(result.to_tree())

    if is_template:
        original_plan.clean_old_template_runs()
