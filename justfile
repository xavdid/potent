set quiet

_default:
  just --list

[positional-arguments]
run *args:
  uv run -- shellprints "$@"

lint *args:
  uv run -- ruff check {{ args }}

init-command name: && (lint "src/shellprints/__init__.py" "--fix" "--quiet")
  {{ assert(path_exists("src/shellprints/commands/" + name + ".py") == "false", "command `" + name + "` already exists") }}
  cp _meta/command.py.tmpl src/shellprints/commands/{{ name }}.py
  sed -i '' 's/<NAME>/{{ name }}/g' src/shellprints/commands/{{ name }}.py
  sed -i '' $'/# COMMAND IMPORTS/i\\\nfrom shellprints.commands.{{ name }} import app as {{ name }}\\\n' src/shellprints/__init__.py
  sed -i '' $'/# COMMANDS/i\\\napp.add_typer({{ name }})\\\n' src/shellprints/__init__.py

