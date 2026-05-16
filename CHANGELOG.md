# Changelog

## Unreleased

- Print the plan path when creating a command plan using only a filename
- fix a bug that caused the wrong emoji to sometimes be used when reporting a plan run result

## 0.4.0

_released `2026-05-13`_

- add support for re-runnable "command plans", which track when they were last run and automatically reset once per calendar day
- add support for specifying a plan name instead of a full path. If you pass a name, `potent` will look for the corresponding plan in the config directory (e.g. `potent run my-script` tries to run the plan at `~/.config/potent/commands/my-script.plan.json`).

## 0.3.0

_released `2026-05-12`_

### CLI

- ‼️ rename the `summarize` command to `status`
- Add the `--version` cli flag to the root CLI command (& migrate to `cyclopts` from `typer`)
- add the `describe` command to print an overview of a plan
- add the `schema` command to make it easier to access the underlying plan schema

### Operations

- ‼️ rename the `switch-branch` slug to `git-switch` to be more in line with other operations
- ‼️ rename the `name` property to `summary`
- add better summaries to most operations
- add `manual-confirmation` step

## 0.2.2

_released `2026-01-19`_

- Add support for paths under a home directory (`~/...`) for easier sharing of plans
- Add support for specifying a name for `raw-command` operations for use in summaries. Useful for differentiating lots of raw commands from each other.

## 0.2.1

_released `2026-01-17`_

- fix Python 3.14 support
- fix `enable-automerge`'s "squash" option
- correctly mark `enable-automerge`'s `config` as optional
- more gracefully handle trying to run non-existent shell commands
- fix surfacing unescaped text when a command has no output

## 0.2.0

_released `2025-10-30`_

- Initial public release!
- Introduce a CLI to run, init, and reset Plan files
- Add the initial set of Operations
