import json
from pathlib import Path

from potent.plan import Plan

Path(__file__, "..", "..", "..", "..", "schema.json").resolve().write_text(
    json.dumps(Plan.model_json_schema(), indent=2)
)
