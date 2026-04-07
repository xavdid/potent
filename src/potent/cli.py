import typer
from cyclopts import App

from potent.commands.describe import app as describe
from potent.commands.init import app as init
from potent.commands.reset import app as reset
from potent.commands.run import app as run
from potent.commands.schema import app as schema
from potent.commands.status import app as status

# COMMAND IMPORTS ^


app = App(
    help="Idempotently run commands across folders.",
    # hide the completion args
    # add_completion=False,
)


def version_callback(print_version: bool):
    if not print_version:
        return

    from importlib.metadata import version  # noqa: PLC0415

    print(f"v{version('potent')}")
    raise typer.Exit


app.command(run, name="*")
app.command(status, name="*")
app.command(describe, name="*")
app.command(reset, name="*")
app.command(init, name="*")
app.command(schema)
# COMMANDS ^


def main():
    app()


if __name__ == "__main__":
    main()
