from pathlib import Path
from typing import Annotated

import typer

from shellprints.commands._types import PlanJson
from shellprints.shellprint import Shellprint

app = typer.Typer()


@app.command()
def validate(path: PlanJson):
    # can handle this pretty cleanly by pegging the step location and the error type (missing, etc)
    # probably want to hide the traceback though
    # and maybe return
    # can raise typer.Exit(code=int)
    print(Shellprint.model_validate_json(path.read_text()))


# could try to wrap, but the basic error is pretty good:
# from pydantic import ValidationError
# except ValidationError as e:
# print(e.errors()[0])
