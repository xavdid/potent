from typing import Annotated

import typer

from potent.commands.init import app as init
from potent.commands.reset import app as reset
from potent.commands.run import app as run
from potent.commands.schema import app as schema
from potent.commands.summarize import app as summarize

# COMMAND IMPORTS ^


app = typer.Typer(
    no_args_is_help=True,
    help="Idempotently run commands across folders.",
    # hide the completion args
    add_completion=False,
)


def version_callback(print_version: bool):
    if not print_version:
        return

    from importlib.metadata import version  # noqa: PLC0415

    print(f"v{version('potent')}")
    raise typer.Exit


app.add_typer(summarize)
app.add_typer(run)
app.add_typer(reset)
app.add_typer(init)
app.add_typer(schema)
# COMMANDS ^


@app.callback()
# this func name doesn't matter
def version_flag(
    # this name also doesn't matter since all we care about is that there's an arg and its callback is evaluated
    _: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version information and exit.",
        ),
    ] = None,
):
    pass


if __name__ == "__main__":
    app()
