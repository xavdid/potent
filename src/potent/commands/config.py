from cyclopts import App

from potent.util import get_config_path

app = App(name="config", help="Commands for interacting with the config file")


@app.command()
def init():
    """
    Create an empty config file at the correct path.
    """
    config_path = get_config_path()
    if config_path.exists():
        raise ValueError(f"Config file at {config_path} already exists.")

    config_path.write_text(
        "# Configuration for potent\n# https://github.com/xavdid/potent#configuration\n\n# NOTE: options must be supplied under their corresponding command name\n\n[run]\n# ...\n"
    )
    print(f'Created "{config_path}"')
