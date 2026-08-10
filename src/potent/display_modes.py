"""
Some high-level structs that centrally control output verbosity levels
"""

from dataclasses import dataclass
from typing import Literal, Sequence, get_args

from cyclopts import Token

DisplayModeNames = Literal["quiet", "compact", "verbose"]


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
                f"{mode} is not a valid display mode. Options are: {get_args(DisplayModeNames)}"
            )

        return modes_by_name[mode]


QuietDisplayMode = DisplayMode(
    "quiet",
    show_non_error_panels=False,
    show_duplicate_statuses=False,
)

CompactDisplayMode = DisplayMode(
    "compact",
    show_non_error_panels=True,
    show_duplicate_statuses=False,
)

VerboseDisplayMode = DisplayMode(
    "verbose",
    show_non_error_panels=True,
    show_duplicate_statuses=True,
)

_modes = [QuietDisplayMode, CompactDisplayMode, VerboseDisplayMode]

modes_by_name: dict[DisplayModeNames, DisplayMode] = {m.name: m for m in _modes}
