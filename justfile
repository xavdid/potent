set quiet

_default:
  just --list

# regenerate the autodocs
[no-exit-message]
update-docs:
  uv run -- _meta/update_docs.py
  prettier --write --log-level silent README.md

# regenerate the json schema
[no-exit-message]
dump-schema:
  uv run -- _meta/dump_schema.py

docs: update-docs dump-schema

# run unit tests against all supported Python versions
[positional-arguments]
test-versions *args:
  # this handles the build and installs magically - it's very cool
  uv run -- tox -p "$@"

lint *args:
  uv run -- ruff check {{ args }}

_is_valid_python_identifier name:
  {{ assert(name =~ "^[A-Za-z_]*$", "not a valid python identifier") }}

# create new command
init-command name: (_is_valid_python_identifier name) && (lint "src/potent/cli.py" "--fix" "--quiet")
  {{ assert(path_exists("src/potent/commands/" + name + ".py") == "false", "command `" + name + "` already exists") }}
  cp _meta/command.py.tmpl src/potent/commands/{{ name }}.py
  sed -i '' 's/<NAME>/{{ name }}/g' src/potent/commands/{{ name }}.py
  sed -i '' $'/# COMMAND IMPORTS/i\\\nfrom potent.commands.{{ name }} import app as {{ name }}\\\n' src/potent/cli.py
  sed -i '' $'/# COMMANDS/i\\\napp.add_typer({{ name }})\\\n' src/potent/cli.py

# create new operation
init-directrive name: (_is_valid_python_identifier name) && (lint "src/potent/plan.py" "--fix" "--quiet")
  {{ assert(path_exists("src/potent/operationss/" + name + ".py") == "false", "operation `" + name + "` already exists") }}
  cp _meta/operations.py.tmpl src/potent/operationss/{{ name }}.py
  sed -i '' $'/# DIRECTIVE IMPORTS/i\\\nfrom potent.operations.{{ name }} import TKTK\\\n' src/potent/plan.py
  sed -i '' $'/# DIRECTIVES/i\\\n                TKTK,\\\n' src/potent/plan.py

[confirm("This will release the package as written. Have you already run `uv version`? (yN)")]
release:
  rm -rf dist
  uv build
  uv publish
