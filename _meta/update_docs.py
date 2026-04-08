import inspect
from itertools import chain
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from cyclopts import App, Parameter

from potent.cli import app as CLI
from potent.plan import Plan

if TYPE_CHECKING:
    from potent.operations._base import BaseOperation

# must match the line in readme, so update those together
type DocBlock = Literal["OPERATIONS", "CLI"]


_SKIP_COMMANDS = {"--help", "-h", "--version"}


def _get_command_help(sub_app: App) -> str:
    """Return the short help string for a cyclopts sub-app."""
    if sub_app.help:
        return sub_app.help

    if (fn := sub_app.default_command) and fn.__doc__:
        # First non-empty line of the docstring is the short description.
        return fn.__doc__.strip().splitlines()[0].strip()
    return ""


def _unwrap_annotated(annotation) -> tuple[Any, list[str]]:
    """Split Annotated[T, ...] into (T, [metadata, ...]), or (annotation, [])."""
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        return args[0], list(args[1:])
    return annotation, []


def _format_type(annotation) -> str:
    """Render a type annotation as a compact string, e.g. Literal['a','b'] or str."""
    raw, args = _unwrap_annotated(annotation)

    # special handling for named parameters, like PlanJson being a FILE
    if args and (name := getattr(args[0], "name")):
        return name[0]

    origin = get_origin(raw)

    # Literal['a', 'b'] -> `"a"` | `"b"`
    if origin is type(None):
        return "None"

    if origin is Union:
        inner = get_args(raw)
        parts = [_format_type(t) for t in inner if t is not type(None)]
        return " | ".join(parts)

    if origin is Literal:
        choices = get_args(raw)
        return " | ".join(
            f'`"{c}"`' if isinstance(c, str) else f"`{c}`" for c in choices
        )

    # plain builtins
    if hasattr(raw, "__name__"):
        return raw.__name__

    return str(raw)


def _is_flag(annotation, default) -> bool:
    """A bool param with a bool default is a flag."""
    raw, _ = _unwrap_annotated(annotation)
    return raw is bool or (get_origin(raw) is None and isinstance(default, bool))


def _format_default(default: Any) -> str:
    if default is inspect.Parameter.empty or default is None:
        return ""
    if isinstance(default, str):
        return f'`"{default}"`'
    return f"`{default}`"


def _document_command_params(fn) -> list[dict[str, Any]]:
    """Return structured param info for a cyclopts command function."""
    if fn is None:
        return []

    hints = get_type_hints(fn, include_extras=True)

    sig = inspect.signature(fn)
    result = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue

        annotation = hints.get(name, param.annotation)
        default = param.default
        has_default = default is not inspect.Parameter.empty

        # keyword-only params (after *) are options; positional are arguments
        is_option = param.kind in (inspect.Parameter.KEYWORD_ONLY,)
        _, metadata = _unwrap_annotated(annotation)
        cyclopts_param = next((m for m in metadata if isinstance(m, Parameter)), None)
        annotated_help = (
            cyclopts_param.help if cyclopts_param and cyclopts_param.help else ""
        )

        result.append(
            {
                "name": name,
                "type": _format_type(annotation),
                "required": not has_default,
                "default": _format_default(default) if has_default else "",
                "help": annotated_help,
                "is_flag": _is_flag(annotation, default) and is_option,
                "is_option": is_option,
            }
        )

    return result


def _generate_command_doc(sub_app: App, parent_name: str | None = None) -> list[str]:
    name = sub_app.name[0]

    heading = f"`{parent_name} {name}`" if parent_name else f"`{name}`"
    doc: list[str] = [f"### {heading}", ""]

    if help_text := _get_command_help(sub_app):
        doc += [help_text.strip(), ""]

    # Sub-commands (nested apps)
    if real_children := [k for k in sub_app if k not in _SKIP_COMMANDS]:
        doc += ["It includes the following subcommands:", ""]
        doc += [f"- `{c}`" for c in real_children]
        doc.append("")
        for child_name in real_children:
            doc.extend(_generate_command_doc(sub_app[child_name], parent_name=name))

    # Parameters for this command's default_command function
    params = _document_command_params(sub_app.default_command)

    if arguments := [p for p in params if not p["is_option"]]:
        doc += ["#### Arguments", ""]
        for arg in arguments:
            req = "required" if arg["required"] else "optional"
            line = f"- `{arg['name']}` ({arg['type']}, {req})"
            if arg["help"]:
                line += f": {arg['help']}"
            doc.append(line)
        doc.append("")

    if options := [p for p in params if p["is_option"]]:
        doc += ["#### Options", ""]
        for opt in options:
            cli_name = f"--{opt['name'].replace('_', '-')}"
            if opt["is_flag"]:
                line = f"- `{cli_name}`"
            else:
                line = f"- `{cli_name} {opt['type']}`"
            if opt["help"]:
                line += f": {opt['help']}"
            if opt["default"] and not opt["is_flag"]:
                line += f" (default: {opt['default']})"
            doc.append(line)
            doc.append("")

    return doc


def cli_docs() -> list[str]:
    real_commands = sorted(k for k in CLI if k not in _SKIP_COMMANDS)
    return list(
        chain.from_iterable(_generate_command_doc(CLI[name]) for name in real_commands)
    )


def operations_markdown() -> list[str]:
    # the actual list of operations is fairly deeply nested
    annotated = get_args(Plan.model_fields["operations"].annotation)[0]
    union = get_args(annotated)[0]
    operations: list[BaseOperation] = sorted(get_args(union), key=lambda d: d.__name__)

    return [
        # markdown table with operations names and slugs
        "### Available Operations",
        "|Slug|Requires Config?|",
        "|---|---|",
        *("|".join(o.to_markdown_summary()) for o in operations),
        # full docs
        *chain.from_iterable(o.to_markdown() for o in operations),
    ]


BUILDERS: dict[DocBlock, Callable[[], list[str]]] = {
    "OPERATIONS": operations_markdown,
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
