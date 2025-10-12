import typer

from potent.commands.dump_schema import app as dump_schema
from potent.commands.reset import app as reset
from potent.commands.run import app as run
from potent.commands.summarize import app as summarize

# COMMAND IMPORTS ^

app = typer.Typer(
    no_args_is_help=True,
    help="Idempotently run commands across folders.",
    # hide the completion args
    add_completion=False,
)

app.add_typer(summarize)
app.add_typer(dump_schema)
app.add_typer(run)
app.add_typer(reset)
# COMMANDS ^


def main():
    app()
