import tomllib
from functools import partial
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter, validators

from potent.docs import operations_markdown, update_file

app = App(name="docs", help="Commands to interact with auto-documentation.")


@app.command()
def generate(
    into_file: Annotated[
        Path | None,
        Parameter(
            validator=validators.Path(exists=True),
            env_var=None,
            help="If present, generate docs between the start and end markers in this file. Otherwise, prints to stdout.",
        ),
    ] = None,
    /,
):
    """
    Generate markdown docs for all installed operations. If you're developing a plugin, running this in that directory will only show the operations your plugin contributes.
    """

    from_plugin = None

    if (pyproject_toml_path := Path("pyproject.toml")).exists():
        project_toml = tomllib.loads(pyproject_toml_path.read_text())
        if (name := project_toml.get("project", {}).get("name")) and name.startswith(
            "potent-"
        ):
            from_plugin = name

    if into_file:
        update_file(
            into_file, {"OPERATIONS": partial(operations_markdown, plugin=from_plugin)}
        )
    else:
        print("\n".join(operations_markdown(plugin=from_plugin)))
