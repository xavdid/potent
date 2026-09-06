from pathlib import Path

import rich
from cyclopts import App
from rich.tree import Tree

from potent.plan import get_plans_from_path
from potent.util import get_command_dir

app = App()


@app.command(name="list")
def list_commands():
    """
    List all available plans (both global commands and plans in this directory).
    """

    root = Tree(
        "Currently available plans. Run `[bold cyan]potent run <name>[/]` to invoke any of them."
    )

    def print_tree(path: Path, label: str, trim_filename: bool, color: str):
        tree = None
        for p in get_plans_from_path(path):
            if not tree:
                tree = root.add(label)

            plan_name = p.plan_name(short_path=True)
            if trim_filename:
                plan_name = plan_name[:-10]

            tree.add(
                f"[bold {color}]{plan_name}[/]{f' ({p.comment})' if p.comment else ''}"
            )

    print_tree(get_command_dir(), label="global", trim_filename=True, color="blue")
    print_tree(Path(), label="local", trim_filename=False, color="yellow")

    rich.print(root)
