# Changelog

## Unreleased

_released `TBD`_

- When running, consecutive skipped steps are grouped under a single panel to save space
- Recolor `halted` steps in output to be yellow (halted) instead of red (failed) (even though they're still failed under the hood)

## 0.7.0

_released `2026-07-23`_

- ❗ rename `enable-automerge` to `set-automerge` and add `config.enable` (which defaults to `true` to patch previous behavior)
- Skip printing all steps for when identical to previous directory for `run` and `status` commands (disable with `--skip-collapse`)
- add a "⏸️ Halted" mode to `potent status`. This is purely presentational and involves no schema changes ([#4](https://github.com/xavdid/potent/pull/4))
- raise the message truncation limit for `git-commit` and `raw-command` when printing a plan

## 0.6.0

_released `2026-07-14`_

- add `change-pr-status` operation for moving PRs between draft and ready.
- add optional `reason` to `manual-confirmation` operation for better summaries.
- fix `potent status` crash when adding a new operation to an otherwise completed plan.

## 0.5.0

_released `2026-05-21`_

- ❗ remove the `path` argument for `potent schema dump` and instead print to stdout. You can redirect this to a file to restore the original behavior.
- Print the plan path when creating a command plan using only a short name
- fix a bug that caused the wrong emoji to sometimes be used when reporting a plan run result ([#2](https://github.com/xavdid/potent/pull/2))
- `manual-confirmation` steps now show their comment, if any

This release also contains some changes to the Python API (which isn't considered stable, but is probably worth mentioning just in case):

- ❗ Remove the `Plan.open()` context manager. Use `Plan.from_path(path)` when working with a file
- ❗ rename the `short_plan` kwarg in `Plan.run()` to `short_path`
- ❗ change the return type of `Plan.run()` to a new `RunSummary` class that can _print_ the `Tree` that was returned before
- ❗ add a `renderer` kwarg to `Plan.run()`. This is technically backwards compatible except that calling it with the default args will no longer show any output. Use `Plan.

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
