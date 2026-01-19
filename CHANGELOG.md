# Changelog

## Unreleased

_released `TBD`_

- Add support for paths under a home directory (`~/...`) for easier sharing of plans
- Add support for specifying a name for `raw-command` operations for use in summaries. Useful for differentiating lots of raw commands from each other.

## 0.2.1

_released `2026-01-17`_

- fix Python 3.14 support
- fix `enable-automerge`'s "squash" option
- correctly mark `enable-automerge`'s `config` as optional
- more gracefully handle trying to run missing commands
- fix surfacing unescaped text when a command has no output

## 0.2.0

_released `2025-10-30`_

- Initial public release!
- Introduce a CLI to run, init, and reset Plan files
- Add the initial set of Operations
