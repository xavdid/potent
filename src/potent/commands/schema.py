import json
from pathlib import Path
from typing import Annotated

import typer

from potent.plan import Plan

app = typer.Typer(
    name="schema", help="Tools to programatically access the plan schema."
)


@app.command()
def url():
    """
    Print the versioned url of Potent's JSON schema. Useful for getting in-editor completions or performing external validations.
    """
    # TODO: warn about plugins
    from importlib.metadata import version  # noqa: PLC0415

    # https://raw.githubusercontent.com/xavdid/potent/refs/tags/v0.2.2/schema.json
    print(
        f"https://raw.githubusercontent.com/xavdid/potent/refs/tags/v{version('potent')}/schema.json"
    )


@app.command()
def dump(path: Annotated[Path, typer.Argument(dir_okay=False, resolve_path=True)]):
    """
    Dump the current. While the versioned url is simpler to use, this schema will include any plugins you have, making it more complete & accurate for your use case.
    """
    path.write_text(json.dumps(Plan.model_json_schema(), indent=2))
