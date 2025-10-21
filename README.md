# potent

> /ˈpōtnt/
>
> adjective
>
> having great power, influence, or effect.

A CLI for running idem**potent** shell scripts across multiple directories.

## Demo

```
TKTK
```

## Install

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

Scripts are run as Plan files. They've got the extension `.plan.json`, but are standard json otherwise.

## Directives

<!-- BEGIN:DIRECTIVES -->

### CleanWorkdir

Slug: `"clean-status"`

### CreatePR

Creates a branch if missing. Re-verifies that you're on that branch during every run.

Slug: `"create-pr"`

#### Config

| name          | type     | description                                                                                                            | default (if optional) |
| ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `title`       | str      | The title of the PR.                                                                                                   | `PydanticUndefined`   |
| `body_text`   | Optional | A string that will be used as the body of the PR. Exactly one of `body_text` or `body_file` is required.               |                       |
| `body_file`   | Optional | The path to a readable file containing the full body of the PR. Exactly one of `body_text` or `body_file` is required. |                       |
| `draft`       | bool     | None                                                                                                                   |                       |
| `base_branch` | Optional | None                                                                                                                   |                       |

### EnableAutomerge

Creates

Slug: `"enable-automerge"`

#### Config

| name   | type    | description | default (if optional) |
| ------ | ------- | ----------- | --------------------- |
| `mode` | Literal | None        | `squash`              |

### GitAdd

Creates a branch if missing. Re-verifies that you're on that branch during every run.

Slug: `"git-add"`

#### Config

| name      | type | description                                                                      | default (if optional) |
| --------- | ---- | -------------------------------------------------------------------------------- | --------------------- |
| `all`     | bool | If `true`, add stage files. Exactly one of `all` or `pattern` must be specified. |                       |
| `pattern` | str  | The file(s) to stage. Exactly one of `all` or `pattern` must be specified.       |                       |

### GitCommit

Creates a branch if missing. Re-verifies that you're on that branch during every run.

Slug: `"git-commit"`

#### Config

| name      | type | description | default (if optional) |
| --------- | ---- | ----------- | --------------------- |
| `message` | str  | None        | `PydanticUndefined`   |

### GitPull

Slug: `"git-pull"`

### GitPush

Creates a branch if missing. Re-verifies that you're on that branch during every run.

Slug: `"git-push"`

### RawCommand

Runs a bash command. The step is successful if it exits 0 and fails otherwise.

Slug: `"raw-command"`

#### Config

| name        | type | description                                                                                                                        | default (if optional) |
| ----------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `arguments` | list | The arguments that will be passed into Python's [subprocess.run](https://docs.python.org/3/library/subprocess.html#subprocess.run) | `PydanticUndefined`   |

### SwitchBranch

Creates a branch if missing. Re-verifies that you're on that branch during every run.

Slug: `"switch-branch"`

#### Config

| name                | type | description                                                 | default (if optional) |
| ------------------- | ---- | ----------------------------------------------------------- | --------------------- |
| `branch`            | str  | branch name                                                 | `PydanticUndefined`   |
| `create_if_missing` | bool | If true, tries creating the branch if switching to it fails |                       |

<!-- END:DIRECTIVES -->

some after text
