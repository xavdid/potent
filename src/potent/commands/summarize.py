import rich
import typer

from potent.commands._types import PlanJson
from potent.plan import Plan

app = typer.Typer()


@app.command()
def summarize(path: PlanJson):
    # can handle this pretty cleanly by pegging the step location and the error type (missing, etc)
    # probably want to hide the traceback though
    # and maybe return
    # can raise typer.Exit(code=int)
    # print(f"Shellprint @ {str(path)}")
    # print(Shellprint.from_path(path))
    rich.print(Plan.from_path(path).summarize(path))


# could try to wrap, but the basic error is pretty good:
# from pydantic import ValidationError
# except ValidationError as e:
# print(e.errors()[0])
