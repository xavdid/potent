import rich
from cyclopts import App
from rich.tree import Tree

from potent.plan import Plan, get_available_templates

app = App()


@app.command(name="list")
def list_commands():
    """
    List all available plans (both global commands and plans in this directory).
    """

    root = Tree(
        "Currently available plans. Run `[bold cyan]potent run <name>[/]` to invoke any of them."
    )

    def print_tree(plans: list[Plan], label: str, trim_filename: bool, color: str):
        tree = None
        for p in plans:
            if not tree:
                tree = root.add(label)

            plan_name = p.plan_name(short_path=True)
            if trim_filename:
                plan_name = plan_name[:-10]

            tree.add(
                f"[bold {color}]{plan_name}[/]{f' ({p.comment})' if p.comment else ''}"
            )

    global_commands, local_commands = get_available_templates()

    print_tree(global_commands, label="global", trim_filename=True, color="blue")
    print_tree(local_commands, label="local", trim_filename=False, color="yellow")

    rich.print(root)
