import os
from pathlib import Path
from typing import Annotated, Sequence

from cyclopts import Parameter, Token, validators


def is_plan_json(_, path: Path) -> None:
    if path.suffixes != [".plan", ".json"]:
        raise ValueError("File must have a `.plan.json` extension")


def get_command_dir() -> Path:
    # from: https://github.com/srstevenson/xdg-base-dirs/blob/ee1b8c41a29bc21f727c7bba54ad56788127f19b/src/xdg_base_dirs/__init__.py#L51
    config_root = Path.home() / ".config"
    if (value := os.environ.get("XDG_CONFIG_HOME")) and (
        config_override_dir := Path(value)
    ).is_absolute():
        config_root = config_override_dir

    return config_root / "potent" / "commands"


def pathify(_, tokens: Sequence[Token]) -> Path:
    """
    Input could be a path-looking thing or a string that's a shortcut to a path (but not fully qualified). Either way, turn it into a path.
    """
    token = tokens[0].value

    # if it looks like a Path, assume it is (and validate later)
    if "." in token or "/" in token:
        return Path(token)

    # assume it's a shortcut to a command
    return get_command_dir() / f"{token}.plan.json"


# this must not be a type= annotation and you must not use a special cyclopts type, like ExistingJsonPath, since it shadows my parameter
PlanJson = Annotated[
    Path,
    Parameter(
        name="FILE",
        converter=pathify,
        validator=[
            is_plan_json,
            validators.Path(ext="json", exists=True, dir_okay=False),
        ],
        help="The location of a `.plan.json` file. Can be a full path or a name. If a name, the named file must exist in the configured command directory.",
    ),
]
