from typing import get_args

from potent.display_modes import DisplayModeNames, modes_by_name


def test_all_modes_are_accounted_for_once():
    # for each literal type, there should be a matching dataclass
    assert set(modes_by_name) == set(get_args(DisplayModeNames))
