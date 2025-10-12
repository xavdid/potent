import json
from pathlib import Path

import typer

from potent.plan import Plan

app = typer.Typer()


@app.command()
def dump_schema():
    Path(__file__, "..", "..", "..", "..", "schema.json").resolve().write_text(
        json.dumps(Plan.model_json_schema(), indent=2)
    )
