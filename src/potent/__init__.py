import typer

from potent.commands.init import app as init
from potent.commands.reset import app as reset
from potent.commands.run import app as run
from potent.commands.summarize import app as summarize

# COMMAND IMPORTS ^

# TODO: move to a cli file and use this as the real init (for exporting the python API).

app = typer.Typer(
    no_args_is_help=True,
    help="Idempotently run commands across folders.",
    # hide the completion args
    add_completion=False,
)

app.add_typer(summarize)
app.add_typer(run)
app.add_typer(reset)
app.add_typer(init)
# COMMANDS ^


# main entrypoint for the CLI
def main():
    app()
