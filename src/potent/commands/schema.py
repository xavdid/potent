import json

from cyclopts import App

from potent.plan import Plan

app = App(name="schema", help="Tools to programmatically access the plan schema.")


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
def dump():
    """
    Dump the current schema to stdout. While the versioned url is simpler to use, the dumped schema will include any plugins you have installed, making it more complete & accurate for your use case.
    """
    print(json.dumps(Plan.model_json_schema(), indent=2))
