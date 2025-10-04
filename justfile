set quiet

_default:
  just --list

[positional-arguments]
run *args:
  uv run -- shellprints "$@"

lint *args:
  uv run -- ruff check {{ args }}

