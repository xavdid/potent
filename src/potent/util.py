import builtins
import os
import pathlib  # used for pattern matching
import typing
from pathlib import Path  # used for actual python operations


def truthy_list[T](l: list[T]) -> list[T]:
    """
    Return a list with the falsy elements removed
    """
    return list(filter(None, l))


def table_row(l: list[str]) -> str:
    return " | ".join(l).join("||")


def format_annotation(a) -> str:
    match typing.get_origin(a):
        case None:
            return f"`{a.__name__}`"
        case builtins.list:
            return f"`{a}`"
        case typing.Union:
            match args := typing.get_args(a):
                case (inner, type() as maybe_none) if len(
                    args
                ) == 2 and maybe_none is type(None):
                    # it's an optional!
                    match inner:
                        case pathlib.Path:
                            return "`Optional[str]`"
                        case builtins.str:
                            return f"`Optional[{inner.__name__}]`"
                        case annotated if typing.get_origin(inner) is typing.Annotated:
                            return format_annotation(
                                typing.Optional[typing.get_args(annotated)[0]]
                            )
                        case _:
                            raise NotImplementedError(f"unable to format optional: {a}")
                case _:
                    raise NotImplementedError(f"unable to format union: {a}")
        case typing.Literal:
            return f"{' \\| '.join(f'`"{t}"`' for t in typing.get_args(a))}"
        case _:
            raise NotImplementedError(f"unable to format: {a}")


def get_config_dir() -> Path:
    """
    The folder in which we'll store everything stateful
    """
    # from: https://github.com/srstevenson/xdg-base-dirs/blob/ee1b8c41a29bc21f727c7bba54ad56788127f19b/src/xdg_base_dirs/__init__.py#L51
    config_root = Path.home() / ".config"
    if (value := os.environ.get("XDG_CONFIG_HOME")) and (
        config_override_dir := Path(value)
    ).is_absolute():
        config_root = config_override_dir

    return config_root / "potent"


def get_command_dir() -> Path:
    """
    global commands live here
    """
    return get_config_dir() / "commands"


def get_config_path() -> Path:
    return get_config_dir() / "potent.toml"
