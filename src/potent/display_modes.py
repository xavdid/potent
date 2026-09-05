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
        """
        Turns a string into a DisplayMode. is responsible for validation instead of cyclopts
        """

        return modes_by_name[tokens[0].value]


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

modes_by_name = {m.name: m for m in _modes}

DisplayModeFlag = Annotated[
    DisplayMode,
    Parameter(
        name="display-mode",
        converter=DisplayMode.parse,
        choices=display_mode_names,
        accepts_keys=False,
        show_default=False,
    ),
]
