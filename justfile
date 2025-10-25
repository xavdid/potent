set quiet

_default:
  just --list

# regenerate the autodocs
[no-exit-message]
update-docs:
  uv run -- _meta/update_docs.py

# regenerate the json schema
[no-exit-message]
dump-schema:
  uv run -- _meta/dump_schema.py

# used for running the CLI locally
[positional-arguments]
run *args:
  uv run -- potent "$@" example.plan.json

lint *args:
  uv run -- ruff check {{ args }}

_is_valid_python_identifier name:
  {{ assert(name =~ "^[A-Za-z_]*$", "not a valid python identifier") }}

# create new command
init-command name: (_is_valid_python_identifier name) && (lint "src/potent/__init__.py" "--fix" "--quiet")
  {{ assert(path_exists("src/potent/commands/" + name + ".py") == "false", "command `" + name + "` already exists") }}
  cp _meta/command.py.tmpl src/potent/commands/{{ name }}.py
  sed -i '' 's/<NAME>/{{ name }}/g' src/potent/commands/{{ name }}.py
  sed -i '' $'/# COMMAND IMPORTS/i\\\nfrom potent.commands.{{ name }} import app as {{ name }}\\\n' src/potent/__init__.py
  sed -i '' $'/# COMMANDS/i\\\napp.add_typer({{ name }})\\\n' src/potent/__init__.py

# create new directive
init-directrive name: (_is_valid_python_identifier name) && (lint "src/potent/plan.py" "--fix" "--quiet")
  {{ assert(path_exists("src/potent/directives/" + name + ".py") == "false", "directive `" + name + "` already exists") }}
  cp _meta/directive.py.tmpl src/potent/directives/{{ name }}.py
  sed -i '' $'/# DIRECTIVE IMPORTS/i\\\nfrom potent.directives.{{ name }} import TKTK\\\n' src/potent/plan.py
  sed -i '' $'/# DIRECTIVES/i\\\n                TKTK,\\\n' src/potent/plan.py

