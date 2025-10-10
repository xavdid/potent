set quiet

_default:
  just --list

[positional-arguments]
run *args:
  uv run -- potent "$@" example.plan.json

lint *args:
  uv run -- ruff check {{ args }}

init-command name: && (lint "src/potent/__init__.py" "--fix" "--quiet")
  {{ assert(path_exists("src/potent/commands/" + name + ".py") == "false", "command `" + name + "` already exists") }}
  cp _meta/command.py.tmpl src/potent/commands/{{ name }}.py
  sed -i '' 's/<NAME>/{{ name }}/g' src/potent/commands/{{ name }}.py
  sed -i '' $'/# COMMAND IMPORTS/i\\\nfrom potent.commands.{{ name }} import app as {{ name }}\\\n' src/potent/__init__.py
  sed -i '' $'/# COMMANDS/i\\\napp.add_typer({{ name }})\\\n' src/potent/__init__.py

