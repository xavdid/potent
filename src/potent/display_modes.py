"""
Some high-level structs that centrally control output verbosity levels
"""

from dataclasses import dataclass
from typing import Annotated, Literal, Sequence, get_args

from cyclopts import Parameter, Token

# don't need this type if it's just for key names? Could be dict keys
DisplayModeNames = Literal["quiet", "standard", "verbose"]
display_mode_names = get_args(DisplayModeNames)


@dataclass
class DisplayMode:
    name: DisplayModeNames
    show_non_error_panels: bool
    show_duplicate_statuses: bool

    @staticmethod
    def parse(_, tokens: Sequence[Token]) -> "DisplayMode":
        # turns a string into a
        # is responsible for validation instead of cyclopts
        mode = tokens[0].value
        if mode not in modes_by_name:
            raise ValueError(
                f"{mode} is not a valid display mode. Options are: {display_mode_names}"
            )

        return modes_by_name[mode]


QuietDisplayMode = DisplayMode(
    "quiet",
    show_non_error_panels=False,
    show_duplicate_statuses=False,
)

StandardDisplayMode = DisplayMode(
    "standard",
    show_non_error_panels=True,
    show_duplicate_statuses=False,
)

VerboseDisplayMode = DisplayMode(
    "verbose",
    show_non_error_panels=True,
    show_duplicate_statuses=True,
)

_modes = [QuietDisplayMode, StandardDisplayMode, VerboseDisplayMode]

modes_by_name: dict[DisplayModeNames, DisplayMode] = {m.name: m for m in _modes}

DisplayModeFlag = Annotated[
    DisplayMode,
    Parameter(
        name="display-mode",
        converter=DisplayMode.parse,
        # https://github.com/BrianPugh/cyclopts/issues/886
        help=f"Controls how the results are displayed. [choices:  {', '.join(display_mode_names)}] (default: standard)",
        accepts_keys=False,
        show_default=False,
    ),
]
