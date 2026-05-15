from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter, validators

from potent.commands._types import get_command_dir, is_plan_json, pathify
from potent.plan import CommandConfig, Plan, PlanConfig

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
    Create an empty plan at the specified path. If the path resolves to the config directory, then it defaults to `command` mode. Otherwise, the default of `plan` is used.
    """

    is_command = get_command_dir() in path.parents

    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(
        Plan(
            version="v1",
            operations=[],
            directories=[],
            config=CommandConfig() if is_command else PlanConfig(),
        ).model_dump_json(indent=2)
    )

    if is_command:
        print(f"Created {path}")
