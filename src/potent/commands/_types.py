from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ExistingJsonPath


def is_plan_json(_, value: Path):
    if value.suffixes != [".plan", ".json"]:
        raise ValueError("File must have .plan.json extension")
    return value


type PlanJson = Annotated[
    ExistingJsonPath,
    Parameter(
        validator=is_plan_json,
        help="The location of a `.plan.json` file",
    ),
]
