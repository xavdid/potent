# potent

> /ˈpōtnt/
>
> adjective
>
> having great power, influence, or effect.

A CLI for running (idem)**potent** shell scripts across directories.

Your script runs line-by-line in each directory. If it fails, subsequent runs of the script will pick up with the first command that hasn't run successfully yet.

```
example.plan.json
├── ✅ aardvark
│   ├── ✅ git-status
│   ├── ✅ switch-branch
│   ├── ✅ git-commit
│   └── ✅ git-push
├── ❌ badger
│   ├── ❌ git-status
│   ├── ⌛ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ✅ git-status
    ├── ❌ switch-branch
    ├── ⌛ git-commit
    └── ⌛ git-push
```

## Table of Contents

- [Project Status](#project-status)
- [Install](#install)
- [Plans](#plans)
- [Operations](#operations)
- [Configuration](#configuration)
- [Plugins](#plugins)
- [FAQ](#faq)
- [Demo](#demo)

## Project Status

`potent` is still under active development. It's ready for basic use, but not in production-critical systems.

On the road to `v1.0.0`, expect breaking schema changes, new Operations, small behavior changes, and general stability/productionalization improvements.

Before we reach `1.0.0`, there may be breaking changes in any release; see the [CHANGELOG](https://github.com/xavdid/potent/blob/main/CHANGELOG.md) for more details.

## Install

Potent is available on PyPI: https://pypi.org/project/potent/. It's installed as a CLI using one of these tools:

[uv](https://docs.astral.sh/uv/guides/tools/):

```
uv tool install potent
```

[Homebrew](https://brew.sh/):

```
brew install xavdid/projects/potent
```

[pipx](https://pipx.pypa.io/stable/):

```
pipx install potent
```

## Plans

A bash script is stored as a Plan file. They're standard JSON with the extension `.plan.json`.

Plans have three main sections:

- a list of directories in which the Plan will run
- a list of Operations to perform in those directories
- an optional key-value store mapped to each directory

Plan files must conform to The Schema so that the invalid operations are surfaced early and loudly.

### Directories

Potent support both absolute directories (`/Users/somename/path/to/dir`) and directories with a leading `~` (`~/path/to/dir`). In both cases, the **directory must exist** on the filesystem.

### Authoring Plan files

Plans are just JSON, so you can write them by hand or generate them using other programs.

If you'd like in-editor hints, you can tell VSCode (or any other editor that supports JSON Schema) that `*.plan.json` files must conform to the schema by first adding the following to your VSCode settings:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["*.plan.json"],
      "url": "<output of `potent schema url`>"
    }
  ]
}
```

Specifying the schema will help with autocomplete and flag potential errors during manual authoring.

> [!NOTE]
> If you use [plugins](#using-plugins), you'll need a slightly different approach. See [below](#editor-validation-with-plugins).

### Template Plans

Template plans are special plan variant that creates a non-template copy when run instead of modifying the original. A new copy is created each calendar day. They're useful for plans you want to run periodically but are still idempotent within a daily window. For example, running `git pull` on a bunch of directories.

Because the copy is run & modified instead of the original, template plans are great for sharing plans between teammates.

Template plans are declared just like normal ones, but have `config.mode == "template"`:

```json
{
  "config": {
    "mode": "template"
  },
  "version": "v1",
  "operations": [
    {
      "slug": "git-status"
    }
  ],
  "directories": [
    "~/projects/potent-demo/aardvark",
    "~/projects/potent-demo/badger"
  ]
}
```

The most recent 15 copies of a given plan are kept. Older ones are auto-pruned after each `potent run`.

Copies of a template live in `XDG_CONFIG_HOME/potent/template-runs/` and include both the calendar date and an escaped version of the the path to the template, like `~/.config/potent/template-runs/2026-10-18_|Users|david|.config|potent|templates|example.plan.json`.

> [!WARNING]
> Template executions are idempotent based the **calendar date of your local machine**. As a result, running a template at 11:59pm and running it again at 12:01am will cause the plan to start from scratch.
>
> To avoid this, run the created copy directly for runs after the first (e.g. `potent run ~/.config/potent/template-runs/2026-10-18_|Users|<...>|example.plan.json`).

### Plans as CLI input

Most CLI commands accept a plan as their main argument. You can pass either a path to a plan file (like `~/Desktop/my-plan.plan.json`) or a simple string. In the latter case, `potent` will look in its config directory for a plan with the corresponding name. For example, `potent run my-script` tries to run the plan at `~/.config/potent/templates/my-script.plan.json`.

The config directory respects the `XDG_CONFIG_HOME` environment variable.

## Operations

Each Operation is identified by its unique `slug` field. Each of the Operations below describes a single bash command with well-defined (and validated) arguments. If you need more flexibility, check out the [raw command](#rawcommand) Operation.

### Variables

Any operation config that takes a string can also accept a variable value. These can be any string and are wrapped in double curly braces, like `{{ example }}` (whitespace optional).

At runtime, values are replaced with the corresponding entry from the plan's `data` property, if present. Missing values will fail the operation at runtime. For example, running:

```json
{
  "operations": [
    {
      "slug": "git-switch",
      "config": {
        "branch": "feature-{{ name }}"
      }
    }
  ],
  "directories": [
    "~/projects/potent-demo/aardvark",
    "~/projects/potent-demo/badger"
  ],
  "data": {
    "~/projects/potent-demo/aardvark": {
      "name": "bruce"
    }
  }
}
```

would produce `git switch feature-bruce` in `aardvark` and a runtime error in `badger`.

Some operations can populate the `data` property at runtime, or you can hand write those values when creating your plan.

<!-- BEGIN:OPERATIONS -->

### Available Operations

| Slug                                         | Requires Config? |
| -------------------------------------------- | ---------------- |
| [`assert-branch`](#AssertBranch)             | ✅ Reqiured      |
| [`change-pr-status`](#ChangePrStatus)        | ☑️ Optional      |
| [`create-pr`](#CreatePR)                     | ✅ Reqiured      |
| [`git-add`](#GitAdd)                         | ☑️ Optional      |
| [`git-commit`](#GitCommit)                   | ✅ Reqiured      |
| [`git-pull`](#GitPull)                       | ∅ None           |
| [`git-push`](#GitPush)                       | ∅ None           |
| [`git-status`](#GitStatus)                   | ∅ None           |
| [`git-switch`](#GitSwitch)                   | ✅ Reqiured      |
| [`manual-confirmation`](#ManualConfirmation) | ☑️ Optional      |
| [`raw-command`](#RawCommand)                 | ✅ Reqiured      |
| [`set-automerge`](#SetAutomerge)             | ☑️ Optional      |

### AssertBranch

Fails if the current git branch doesn't match the configured one. Useful for ensuring a plan is always run against the intended branch. Helpful if you've been working in a directory and want to be sure a plan only runs against a specific branch.

> [!NOTE]
> This operation will be executed on every run, not just until it succeeds.

**Slug**: `assert-branch`

#### Config

| name     | type  | description | default (if optional) |
| -------- | ----- | ----------- | --------------------- |
| `branch` | `str` | branch name |                       |

### ChangePrStatus

Change the readiness status of a PR. Moves it from draft -> "ready to review" by default, but can also move it back to draft.

> [!IMPORTANT]
> Requires the `gh` CLI to be installed.

**Slug**: `change-pr-status`

#### Config (optional)

| name        | type                   | description                                               | default (if optional) |
| ----------- | ---------------------- | --------------------------------------------------------- | --------------------- |
| `to_status` | `"ready"` \| `"draft"` | Whether to mark the PR as ready or move it back to draft. | `"ready"`             |

### CreatePR

Creates a pull request using the `gh` CLI.

> [!IMPORTANT]
> Requires the `gh` CLI to be installed.

**Slug**: `create-pr`

#### Config

| name          | type            | description                                                                                                                     | default (if optional) |
| ------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `title`       | `str`           | The title of the PR.                                                                                                            |                       |
| `body_text`   | `Optional[str]` | A string that will be used as the body of the PR. Exactly one of `body_text` or `body_file` is required.                        | `None`                |
| `body_file`   | `Optional[str]` | The absolute path to a readable file containing the full body of the PR. Exactly one of `body_text` or `body_file` is required. | `None`                |
| `draft`       | `bool`          | Whether to open the PR in draft mode.                                                                                           | `False`               |
| `base_branch` | `Optional[str]` | The branch that you want to merge your changes into. Defaults to the repo's default branch.                                     | `None`                |

### GitAdd

Stages files in git.

**Slug**: `git-add`

#### Config

| name      | type   | description                                                                                                                                              | default (if optional) |
| --------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `all`     | `bool` | If `true`, add stage files. Exactly one of `all` or `pattern` must be specified.                                                                         | `False`               |
| `pattern` | `str`  | The file(s) to stage. Is processed as a [Python glob](https://docs.python.org/3/library/glob.html). Exactly one of `all` or `pattern` must be specified. | `""`                  |

### GitCommit

Commits staged files in git.

**Slug**: `git-commit`

#### Config

| name          | type   | description                                          | default (if optional) |
| ------------- | ------ | ---------------------------------------------------- | --------------------- |
| `message`     | `str`  | Commit message, submitted as is.                     |                       |
| `allow_empty` | `bool` | If true, allows commits without changed/added files. | `False`               |

### GitPull

Pull from the remote repository.

**Slug**: `git-pull`

### GitPush

Push to the remote repository.

**Slug**: `git-push`

### GitStatus

Ensures that you have a clean working directory. If there are any modified or un-staged files, this step fails.

**Slug**: `git-status`

### GitSwitch

Switches the local git branch. Can optionally create it if it's missing.

**Slug**: `git-switch`

#### Config

| name                | type   | description                                                 | default (if optional) |
| ------------------- | ------ | ----------------------------------------------------------- | --------------------- |
| `branch`            | `str`  | branch name                                                 |                       |
| `create_if_missing` | `bool` | If true, tries creating the branch if switching to it fails | `False`               |

### ManualConfirmation

A step that always fails. To advance your plan, manually edit the plan file so each directory succeeds.

Useful for putting pauses into a multi-phase plan.

**Slug**: `manual-confirmation`

#### Config (optional)

| name     | type            | description                      | default (if optional) |
| -------- | --------------- | -------------------------------- | --------------------- |
| `reason` | `Optional[str]` | User-facing reason for the pause | `None`                |

### RawCommand

Runs a shell command. The step succeeds if the command exits 0 and fails otherwise. Useful for operations that potent doesn't support natively.

**Slug**: `raw-command`

#### Config

| name                  | type            | description                                                                                                                                      | default (if optional) |
| --------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| `arguments`           | `list[str]`     | The arguments that will be passed into Python's [subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run)             |                       |
| `name`                | `Optional[str]` | A name used to disambiguate this step in summaries. Useful if you have many `raw-command`s.                                                      | `None`                |
| `write_output_to_key` | `Optional[str]` | If specified, save a trimmed copy of the output to the `data` property under this key. Will save _all_ output, so only use when output is short. | `None`                |

### SetAutomerge

Sets (or un-sets) auto-merge for the PR corresponding to the current branch.

> [!IMPORTANT]
> Requires the `gh` CLI to be installed.

**Slug**: `set-automerge`

#### Config (optional)

| name     | type                    | description                           | default (if optional) |
| -------- | ----------------------- | ------------------------------------- | --------------------- |
| `enable` | `bool`                  | Whether to set (or unset) auto-merge. | `True`                |
| `mode`   | `"merge"` \| `"squash"` | Sets the merge strategy for the PR.   | `"squash"`            |

<!-- END:OPERATIONS -->

## CLI Commands

<!-- BEGIN:CLI -->

### `config`

Commands for interacting with the config file

It includes the following subcommands:

- `init`

### `config init`

Create an empty config file at the correct path.

### `describe`

Print basic info about the plan, including the directories on which it acts and the steps involved.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file. Can be a full path or a name. If a name, the named file must exist in the configured command directory.

### `docs`

Commands to interact with auto-documentation.

It includes the following subcommands:

- `generate`

### `docs generate`

Generate markdown docs for all installed operations. If you're developing a plugin, running this in that directory will only show the operations your plugin contributes.

#### Arguments

- `into_file` (pathlib.Path | None, optional): If present, generate docs between the start and end markers in this file. Otherwise, prints to stdout.

### `init`

Create an empty plan at the specified path. If the path resolves to the config directory, then it defaults to `command` mode. Otherwise, the default of `plan` is used.

#### Arguments

- `path` (Path, required): The location in which to to create a blank plan file. Can be a full path or a name. If a name, the named file must not exist in the configured command directory.

### `list-commands`

List all available plans (both global commands and plans in this directory).

### `reset`

Reset the progress on a plan file so it can be run again from scratch.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file. Can be a full path or a name. If a name, the named file must exist in the configured command directory.

### `run`

Execute a plan file and then print its status.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file. Can be a full path or a name. If a name, the named file must exist in the configured command directory.
- `display_mode` (display-mode, optional): Controls how the results are displayed.

### `schema`

Commands to programmatically access the plan schema.

It includes the following subcommands:

- `url`
- `dump`

### `schema url`

Print the versioned url of Potent's JSON schema. Useful for getting in-editor completions or performing external validations.

### `schema dump`

Dump the current schema to stdout. While the versioned url is simpler to use, the dumped schema will include any plugins you have installed, making it more complete & accurate for your use case.

### `status`

Print the current state of a plan file, including the progress through each directory.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file. Can be a full path or a name. If a name, the named file must exist in the configured command directory.
- `display_mode` (display-mode, optional): Controls how the results are displayed.

<!-- END:CLI -->

## Configuration

All CLI flags can be read from an via environment variable or a dedicated configuration file. They are parsed & merged with the following precedence, stopping at the first one found:

1. CLI flags
2. environment variables
3. config file
4. default value

### Environment

Set flags using an environment variable key that combines, `potent`, the command, and the flag name, separated by underscores. For instance, the `display-mode` flag for `potent run` can be set using `POTENT_RUN_DISPLAY_MODE=... potent run`.

### File

Potent reads the `potent.toml` file from `XDG_CONFIG_HOME/potent/potent.toml`, defaulting to `~/.config/potent/potent.toml` if `XDG_CONFIG_HOME` is not set.

Inside the toml file, each top-level table is a command name. The keys & values under that correspond to specific flags.

For instance, the `display-mode` flag for `potent run` can be stored as:

```toml
# ~/.config/potent/potent.toml

[run]
display-mode = 'compact'
```

## Display Modes

The tool has a few ways to show data as scripts are running. Here are the features each mode sets:

| mode                 | panels shown               | summary de-duplicated |
| -------------------- | -------------------------- | --------------------- |
| `quiet`              | only errors                | yes                   |
| `standard` (default) | all, skipped steps grouped | yes                   |
| `verbose`            | all                        | no                    |

## Using Plugins

3rd party packages can contribute additional [Operations](#operations) to your potent plans. Potent will automatically detect valid plugins that are installed alongside it:

```shell
uv tool install potent --with potent-example
```

Then, write your plan as normal. The slugs from 3rd-party Operations will start with the plugin name and a period:

```jsonc
{
  // ...
  "operations": [
    {
      "slug": "potent-example.echo",
    },
  ],
}
```

### Editor Validation with Plugins

If you use the in-editor validation described [above](#authoring-plan-files), you'll need to generate your schema instead of using the public one. Do do that:

```shell
# after installing a plugin
potent schema dump > my-schema.json
```

And then point VSCode to that file:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["*.plan.json"],
      "url": "./my-schema.json"
    }
  ]
}
```

## Authoring Plugins

> [!TIP]
> There's a repo template to get you started: https://github.com/xavdid/potent-plugin-template

### Identifying as a Plugin

Your plugin should supply a list of classes that inherit from `BaseOperation`. You expose this via the `[project.entry-points.potent]` key in your `pyproject.toml`. Underneath should be a key & [object reference](https://packaging.python.org/en/latest/specifications/entry-points/#data-model) pointing to your list:

```toml
[project.entry-points.potent]
operations = 'potent_plugin:operations'
```

### Writing an Operation

Each operation inherits from the built-in `BaseOperation` class. The base class provides a number of utility functions and ensures all operations follow a predictable interface. There are a few fields you **must** define:

1. the `slug`. A literal that uniquely identifies your operation. It should start with your package name, followed by a `.`, like `potent-example.something`.
2. the `run` method. It must accept a `potent.Context` argument (see: [context](#run-context)) and must return an `OperationResult`.

Additionally, you _should_ define:

3. The `summary` method, to disambiguate between multiple instances of this operation in a plan. This is strongly recommended if your operation takes a config object.
4. A docstring under your class, which can be picked up by documentation generators.

Lastly, you _may_ define:

5. A nested `OpConfig` class, which provides validated input to your operation. If present, it **must** be declared under the `config` key. It's accessible inside the `run` method as `self.config`.
6. A set of strings, declared as `ignored_fields_for_compare: ClassVar[set[str]] = set([...])`, to note which (if any) properties should be ignored when comparing two `Operation`s or `OpConfig`s. These are used in divergence calculations for [template plans](#template-plans). You should only add field names to this set that have no runtime implications (for example, the `name` field on [raw-command](#rawcommand), which is just used in summarization).

Here's an example that uses all the properties:

```py
from pathlib import Path
from typing import Literal, override, ClassVar

from potent import BaseConfig, BaseOperation, OperationResult


class EchoOp(BaseOperation):
    # 4
    """
    An example operation that echoes user-defined text.
    """

    # 5
    class OpConfig(BaseConfig):
        text: str
        """
        the text to echo
        """

        name: str
        """
        Used to differentiate between multiple instances of this operation
        """

        # 6
        ignored_fields_for_compare: ClassVar[set[str]] = {"name"}

    # 1
    slug: Literal["potent-plugin-example.echo"] = "potent-plugin-example.echo"
    # 5
    config: OpConfig

    # 2
    @override
    def run(self, context: Context) -> OperationResult:
        cmd = ["echo", self.config.text]
        return context.exec_cmd(cmd)

    # 3
    @property
    @override
    def summary(self) -> str:
        return f"echo ({self.config.name})"
```

### Run `Context`

Each invocation of the `run` method is passed a `Context` object with properties and helpers useful for implementing an operation.

#### properties

- `directory: Path`
  - the directory in which the operation is being run

#### methods

- `exec_cmd(cmd: list[str]) -> OperationResult`
  - a high-level helper for shelling out and running commands. Wraps a call to `exec_raw_cmd` and handles `OperationResult` construction under the hood. Most operations will only need this method. Empty strings are dropped from the `cmd` list.
- `exec_raw_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]`
  - a lower-level function that wraps `subprocess.run` with some good defaults, returning the raw result. Callers are responsible for constructing and returning the `OperationResult` themselves. Empty strings are dropped from the `cmd` list.
- `read_data(key: str) -> int | str | bool`
  - Read a key, returning its value. Raises `DataReadException` if the value isn't present in `data`.
- `write_data(key: str, value: int | str | bool) -> None`
  - Write a key a key to storage. Writes will still get saved if the step fails (as long as `write_data` is called before any exceptions are thrown)

### `OperationResult`

Each operation must report its result. There are 2 required properties:

- `success: bool`, whether the command should be considered successful
- `output: str`, shown to the user. In general, this should be the result of the underlying shell command. But, for some operations (like a clean `git status`) it can make sense to provide information when the underlying command doesn't.

There's also an optional `cmd` argument, which shows the user exactly what command was run for the step. This is useful if you have a lot of config properties and you want to be explicit about the final shape of the command.

Consider using the static `OperationResult.from_process(result: subprocess.CompletedProcess[str], cmd: Optional[list[str]] = None)` constructor, which extracts data from the `CompletedProcess` for you.

### Configurable properties

- `always_rerun: ClassVar[bool]`
  - if `True`, the check is re-run on _every_ plan run instead of just once. Useful for assertions. Defaults to `False`.

## FAQ

### Reading validation messages

The error you get when you have an invalid plan file can take a little getting used to. But don't panic! It's actually pretty easy to read.

The most common error you'll get is an invalid slug. It looks like:

```
ValidationError: 1 validation error for Plan
operations.0
  Input tag 'bad-slug' found using 'slug' does not match any of the expected tags: 'git-pull',
'switch-branch', 'git-status', 'git-add', 'git-commit', 'git-push', 'create-pr',
'enable-automerge', 'raw-command' [type=union_tag_invalid, input_value={'comment': None,
'direct...', 'allow_empty': True}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/union_tag_invalid
```

The lines tell you:

1. what failed to validate
2. its json path (in this case, `operations.0`, the first element of the `steps` array)
3. the expected values (which the input doesn't match)

The next most common is missing a required key, which follows a similar pattern:

```
ValidationError: 1 validation error for Plan
operations.0.git-commit.config.message
  Field required [type=missing, input_value={'allow_empty': True}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/missing
```

Line 2 is now even more descriptive: `operations[0].config.message` is an error of `type=missing`. More simply, a required key isn't there.

The last common error is an extra key:

```
operations.0.git-commit.config.bad_key
  Extra inputs are not permitted [type=extra_forbidden, input_value=True, input_type=bool]
    For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
```

Only expected keys are allowed, and `bad_key` is not expected.

## Demo

Let's say we've got 3 repos, `aardvark`, `badger`, and `camel`. In each one, we want to:

1. ensure we have a clean working directory before proceeding
2. switch to the demo branch
3. create an empty commit
4. push that branch

We can create a [plan](#plans) for that operation, `demo.plan.json`:

```json
{
  "version": "v1",
  "operations": [
    {
      "slug": "git-status"
    },
    {
      "slug": "switch-branch",
      "config": {
        "branch": "demo"
      }
    },
    {
      "slug": "git-commit",
      "config": {
        "message": "a cool demo commit",
        "allow_empty": true
      }
    },
    {
      "slug": "git-push"
    }
  ],
  "directories": ["/potent-demo/a", "/potent-demo/b", "/potent-demo/c"]
}
```

Let's make sure it parses correctly:

```
% potent summarize demo.plan.json

/Users/david/projects/potent/example.plan.json
├── ⌛ aardvark
│   ├── ⌛ git-status
│   ├── ⌛ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
├── ⌛ badger
│   └── same steps as above
└── ⌛ camel
    └── same steps as above
```

Looks good! Let's give it a run:

```
% potent run demo.plan.json

Running /Users/david/projects/potent/example.plan.json

────────────────────────────── 📂 aardvark 📂 ──────────────────────────────
╭─ step: git-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git status --porcelain                                               │
│                                                                          │
│ Working directory clean!                                                 │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: switch-branch ────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git switch demo                                                      │
│                                                                          │
│ Switched to branch 'demo'                                                │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: git-commit ───────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git commit -m "a cool demo commit" --allow-empty                     │
│                                                                          │
│ [demo ef51deb] a cool demo commit                                        │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: git-push ─────────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git push                                                             │
│                                                                          │
│ To github.com:xavdid/potent-demo.git                                     │
│    879eaae..ef51deb  demo -> demo                                        │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯


─────────────────────────────── 📂 badger 📂 ───────────────────────────────
╭─ step: git-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git status --porcelain                                               │
│                                                                          │
│ fatal: not a git repository (or any of the parent directories): .git     │
│                                                                          │
╰─ result: Failed ─────────────────────────────────────────────────────────╯


─────────────────────────────── 📂 camel 📂 ────────────────────────────────
╭─ step: git-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git status --porcelain                                               │
│                                                                          │
│ Working directory clean!                                                 │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: switch-branch ────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git switch demo                                                      │
│                                                                          │
│ fatal: invalid reference: demo                                           │
│                                                                          │
╰─ result: Failed ─────────────────────────────────────────────────────────╯


───────────────────────────────── Summary ──────────────────────────────────
example.plan.json
├── ✅ aardvark
│   ├── ✅ git-status
│   ├── ✅ switch-branch
│   ├── ✅ git-commit
│   └── ✅ git-push
├── ❌ badger
│   ├── ❌ git-status
│   ├── ⌛ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ✅ git-status
    ├── ❌ switch-branch
    ├── ⌛ git-commit
    └── ⌛ git-push
```

Oh no! Everything went great in `aardvark`, but it looks like I forgot to initialize the repo in `badger` and `camel` doesn't have the `demo` branch.

I'll run `git init` in `badger` and `git checkout -b demo` in `camel` to get us back on track. Let's run the script again:

```
Running /Users/david/projects/potent/example.plan.json

────────────────────────────── 📂 aardvark 📂 ──────────────────────────────
☑️ already finished

─────────────────────────────── 📂 badger 📂 ───────────────────────────────
╭─ step: git-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git status --porcelain                                               │
│                                                                          │
│ Working directory clean!                                                 │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: switch-branch ────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git switch demo                                                      │
│                                                                          │
│ fatal: invalid reference: demo                                           │
│                                                                          │
╰─ result: Failed ─────────────────────────────────────────────────────────╯


─────────────────────────────── 📂 camel 📂 ────────────────────────────────
╭─ step: git-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ Already completed                                                        │
│                                                                          │
╰─ result: skipped ────────────────────────────────────────────────────────╯

╭─ step: switch-branch ────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git switch demo                                                      │
│                                                                          │
│ Already on 'demo'                                                        │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: git-commit ───────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git commit -m "a cool demo commit" --allow-empty                     │
│                                                                          │
│  a cool demo commit                                                      │
│                                                                          │
╰─ result: Succeeded ──────────────────────────────────────────────────────╯

╭─ step: git-push ─────────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git push                                                             │
│                                                                          │
│ fatal: No configured push destination.                                   │
│ Either specify the URL from the command-line or configure a remote       │
│ repository using                                                         │
│                                                                          │
│     git remote add <name> <url>                                          │
│                                                                          │
│ and then push using the remote name                                      │
│                                                                          │
│     git push <name>                                                      │
│                                                                          │
╰─ result: Failed ─────────────────────────────────────────────────────────╯


───────────────────────────────── Summary ──────────────────────────────────
example.plan.json
├── ☑️ aardvark
├── ❌ badger
│   ├── ✅ git-status
│   ├── ❌ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ☑️ git-status
    ├── ✅ switch-branch
    ├── ✅ git-commit
    └── ❌ git-push
```

The ✅ marks show what steps we completed this run, while ☑️ denotes a step we completed on a previous run.

`aardvark` was skipped since it was already done. We made progress in `badger` and `camel` despite erroring out because we can't switch branches without commits and there's nothing to push to.

But, I could resume my script from the middle, skipping any completed operations. This is the power of `potent`!
