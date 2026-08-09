from pathlib import Path
from typing import Annotated, Sequence

from cyclopts import Parameter, Token, validators

from potent.util import get_command_dir


def is_plan_json(_, path: Path) -> None:
    if path.suffixes != [".plan", ".json"]:
        raise ValueError("File must have a `.plan.json` extension")


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
