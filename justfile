_default:
  just --list

[positional-arguments]
@run *args:
  uv run -- shellprints "$@"
