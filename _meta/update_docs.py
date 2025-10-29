from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Literal, get_args

import typer
from click import Command, Group, Option

from potent import app as CLI
from potent.plan import Plan

if TYPE_CHECKING:
    from potent.directives._base import BaseDirective

type DocBlock = Literal["DIRECTIVES", "CLI"]


def _get_type_name(param_type: Any) -> str:
    if param_type is None:
        return "TEXT"

    type_name = getattr(param_type, "name", str(param_type))
    if isinstance(type_name, str):
        return type_name.upper()
    return str(type_name).upper()


def _format_default(default: Any) -> str:
    if default is None or default == ():
        return ""
    if isinstance(default, str):
        return f'"{default}"'
    return str(default)


def _document_params(params: list[Any]) -> list[dict[str, str]]:
    documented_params = []

    for param in params:
        param_info = {
            "name": param.name,
            "type": _get_type_name(param.type),
            "required": param.required,
            "default": _format_default(param.default),
            "help": param.help or "",
            "is_flag": isinstance(param, Option) and param.is_flag,
            "is_option": isinstance(param, Option),
        }

        if isinstance(param, Option):
            param_info["opts"] = param.opts
            param_info["secondary_opts"] = param.secondary_opts

        documented_params.append(param_info)

    return documented_params


def _generate_command_doc(cmd: Command) -> list[str]:
    doc = [f"### `{cmd.name}`", ""]

    if cmd.help:
        doc.append(f"{cmd.help}")
        doc.append("")

    if hasattr(cmd, "params") and cmd.params:
        params = _document_params(cmd.params)

        # Arguments
        arguments = [p for p in params if not p["is_option"]]
        if arguments:
            doc.append("#### Arguments")
            doc.append("")
            for arg in arguments:
                required_text = "required" if arg["required"] else "optional"
                doc.append(
                    f"- `{arg['name']}` ({arg['type']}, {required_text}): {arg['help']}"
                )
            doc.append("")

        # Options
        options = [p for p in params if p["is_option"]]
        if options:
            doc.append("#### Options")
            doc.append("")
            for opt in options:
                opt_flags = ", ".join(opt.get("opts", []))
                if not opt_flags:
                    opt_flags = f"--{opt['name']}"

                if opt["is_flag"]:
                    opt_line = f"- `{opt_flags}`"
                else:
                    opt_line = f"- `{opt_flags} {opt['type']}`"

                if opt["help"]:
                    opt_line += f": {opt['help']}"

                if opt["default"] and not opt["is_flag"]:
                    opt_line += f" (default: {opt['default']})"

                doc.append(opt_line)
                doc.append("")

    return doc


def cli_docs() -> list[str]:
    click_group = typer.main.get_command(CLI)

    if not isinstance(click_group, Group):
        # this is sort of silly. all of my commands are actually sub-apps, but they don't really need to be. I could hoist them as a non-breaking change.
        raise ValueError("Expected a root group")

    return list(
        chain.from_iterable(
            _generate_command_doc(cmd)
            for _, cmd in sorted(click_group.commands.items())
        )
    )


def directives_markdown() -> list[str]:
    # the actual list of directives is fairly deeply nested
    annotated = get_args(Plan.model_fields["steps"].annotation)[0]
    union = get_args(annotated)[0]
    directives: tuple[BaseDirective] = get_args(union)

    return list(
        chain.from_iterable(
            d.to_markdown() for d in sorted(directives, key=lambda d: d.__name__)
        )
    )


BUILDERS: dict[DocBlock, Callable[[], list[str]]] = {
    "DIRECTIVES": directives_markdown,
    "CLI": cli_docs,
}


def boundaries(block: DocBlock) -> tuple[str, str]:
    return f"<!-- BEGIN:{block} -->", f"<!-- END:{block} -->"


def update_readme(block: DocBlock):
    readme = Path(__file__, "..", "..", "README.md").resolve()
    lines = readme.read_text().splitlines()

    start_flag, stop_flag = boundaries(block)

    start_index = lines.index(start_flag)
    stop_index = lines.index(stop_flag)

    updated_lines = list(
        chain(lines[: start_index + 1], BUILDERS[block](), lines[stop_index:], [""])
    )

    readme.write_text("\n".join(updated_lines))


if __name__ == "__main__":
    for b in get_args(DocBlock.__value__):
        update_readme(b)
