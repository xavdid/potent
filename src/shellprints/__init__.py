import typer

from shellprints.commands.dump_schema import app as dump_schema
from shellprints.commands.reset import app as reset
from shellprints.commands.run import app as run
from shellprints.commands.validate import app as validate

# COMMAND IMPORTS ^

app = typer.Typer(
    no_args_is_help=True,
    help="Idempotently run commands across folders.",
    # hide the completion args
    add_completion=False,
)

app.add_typer(validate)
app.add_typer(dump_schema)
app.add_typer(run)
app.add_typer(reset)
# COMMANDS ^


def main():
    app()
