from itertools import chain
from pathlib import Path
from typing import get_args

from potent.plan import Plan

# the actual list of directives is fairly deeply nested


START_FLAG = "<!-- BEGIN:DIRECTIVES -->"
STOP_FLAG = "<!-- END:DIRECTIVES -->"

readme = Path(__file__, "..", "..", "README.md").resolve()

annotated = get_args(Plan.model_fields["steps"].annotation)[0]
union = get_args(annotated)[0]
directives = get_args(union)

lines = readme.read_text().splitlines()

start_index = lines.index(START_FLAG)
stop_index = lines.index(STOP_FLAG)


lines = list(
    chain(
        lines[: start_index + 1],
        *(d.to_markdown() for d in sorted(directives, key=lambda d: d.__name__)),
        lines[stop_index:],
    )
)

print(lines)

readme.write_text("\n".join(lines))

# print(GitAdd.to_markdown())
