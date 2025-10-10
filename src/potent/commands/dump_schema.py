import json
from pathlib import Path

import typer

from potent.shellprint import Shellprint

app = typer.Typer()


@app.command()
def dump_schema():
    Path(__file__, "..", "..", "..", "..", "schema.json").resolve().write_text(
        json.dumps(Shellprint.model_json_schema(), indent=2)
    )
