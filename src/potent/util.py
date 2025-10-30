import builtins
import pathlib
import typing


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
