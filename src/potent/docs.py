import sys
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Callable, get_args

from potent.plan import Plan

if TYPE_CHECKING:
    from potent.operations._base import BaseOperation


def boundaries(block) -> tuple[str, str]:
    return f"<!-- BEGIN:{block} -->", f"<!-- END:{block} -->"


def op_is_from_plugin(o: type["BaseOperation"], plugin: str) -> bool:
    if not (slug_field := o.model_fields.get("slug")):
        return False

    if not (slug := slug_field.default):
        return False

    return slug.startswith(f"{plugin}.")


def operations_markdown(plugin: str | None = None) -> list[str]:
    annotated = get_args(Plan.model_fields["operations"].annotation)[0]
    union = get_args(annotated)[0]
    operations: list[type[BaseOperation]] = sorted(
        get_args(union), key=lambda d: d.__name__
    )

    if plugin:
        operations = [o for o in operations if op_is_from_plugin(o, plugin)]

    return [
        # markdown table with operations names and slugs
        "### Available Operations",
        "|Slug|Requires Config?|",
        "|---|---|",
        *("|".join(o.to_markdown_summary()) for o in operations),
        # full docs
        *chain.from_iterable(o.to_markdown() for o in operations),
    ]


def update_file(file: Path, builders: dict[str, Callable[[], list[str]]]):
    for block, builder in builders.items():
        # maybe take a plugin name arg and filter for ops belonging to that plugin? have to figure out who/where will be running this
        lines = file.read_text().splitlines()

        start_flag, stop_flag = boundaries(block)

        try:
            start_index = lines.index(start_flag)
            stop_index = lines.index(stop_flag)
        except ValueError:
            print(
                f'ERR: at least one of "{start_flag}" or "{stop_flag}" was not found in "{str(file)}"'
            )
            sys.exit(1)

        updated_lines = list(
            chain(
                lines[: start_index + 1],
                builder(),
                lines[stop_index:],
                [""],
            )
        )

        file.write_text("\n".join(updated_lines))
