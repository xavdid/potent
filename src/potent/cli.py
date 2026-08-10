import cyclopts
from cyclopts import App

from potent.commands.config import app as config
from potent.commands.describe import app as describe
from potent.commands.init import app as init
from potent.commands.reset import app as reset
from potent.commands.run import app as run
from potent.commands.schema import app as schema
from potent.commands.status import app as status
from potent.util import get_config_path

# COMMAND IMPORTS ^


app = App(
    help="Idempotently run commands across folders.",
    # read settings!
    config=[
        # CLI args have the highest priority
        # env has the highest priority
        cyclopts.config.Env("POTENT_"),
        # then the config file
        cyclopts.config.Toml(get_config_path()),
    ],
)


app.command(run, name="*")
app.command(status, name="*")
app.command(describe, name="*")
app.command(reset, name="*")
app.command(init, name="*")
app.command(schema)
app.command(config)
# COMMANDS ^


def main():
    app()


if __name__ == "__main__":
    main()
