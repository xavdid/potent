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
- [FAQ](#faq)
- [Demo](#demo)

## Project Status

`potent` is still under active development. It's ready for basic use, but not in production-critical systems.

On the road to `v1.0.0`, expect breaking schema changes, new Operations, small behavior changes, and general stability/productionalization improvements.

Before we reach `1.0.0`, there may be breaking changes in any release; see the CHANGELOG for more details.

## Install

Potent is available on PyPI: https://pypi.org/project/potent/. It's typically installed as a CLI using one of these tools:

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

Plans have two main components:

- a list of directories the Plan will run in
- a list of Operations to perform in those directories

Each Operation is identified by its unique `slug` field.

### Directories

Potent support both absolute directories (`/Users/somename/path/to/dir`) and directories with a leading `~` (`~/path/to/dir`). In both cases, the **directory must exist** on the filesystem.

### Authoring Plan files

Plans are just JSON, so you can write them by hand or generate them using other programs.

If you'd like in-editor hints, you can tell VSCode (or any other editor that supports JSON Schema) that `*.plan.json` files must conform to the schema by:

1. running `potent schema url` and copying the output
2. adding the following to your VSCode settings:

```json
"json.schemas": [
  {
    "fileMatch": ["*.plan.json"],
    "url": "<URL GOES HERE>"
  }
]
```

Specifying the schema will help with autocomplete and flag potential errors.

## Operations

Each of the Operations below describes a single bash command with well-defined (and validated) arguments. If you need more flexibility, check out the [raw command](#rawcommand) Operation.

<!-- BEGIN:OPERATIONS -->

### Available Operations

| Slug                                   | Requires Config? |
| -------------------------------------- | ---------------- |
| [`create-pr`](#CreatePR)               | ☑️               |
| [`enable-automerge`](#EnableAutomerge) | ☑️               |
| [`git-add`](#GitAdd)                   | ☑️               |
| [`git-commit`](#GitCommit)             | ☑️               |
| [`git-pull`](#GitPull)                 |
| [`git-push`](#GitPush)                 |
| [`git-status`](#GitStatus)             |
| [`git-switch`](#GitSwitch)             | ☑️               |
| [`raw-command`](#RawCommand)           | ☑️               |

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

### EnableAutomerge

Enables auto-merge for the PR corresponding to the current branch.

> [!IMPORTANT]
> Requires the `gh` CLI to be installed.

**Slug**: `enable-automerge`

#### Config (optional)

| name   | type                    | description                         | default (if optional) |
| ------ | ----------------------- | ----------------------------------- | --------------------- |
| `mode` | `"merge"` \| `"squash"` | Sets the merge strategy for the PR. | `"squash"`            |

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

### RawCommand

Runs a shell command. The step succeeds if the command exits 0 and fails otherwise.

**Slug**: `raw-command`

#### Config

| name        | type            | description                                                                                                                          | default (if optional) |
| ----------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| `arguments` | `list[str]`     | The arguments that will be passed into Python's [subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run) |                       |
| `name`      | `Optional[str]` | A name used to disambiguate this step in summaries. Useful if you have many `raw-command`s.                                          | `None`                |

<!-- END:OPERATIONS -->

## CLI Commands

<!-- BEGIN:CLI -->

### `info`

Print basic info about the plan, including the directories it acts on and the steps involved.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file

### `init`

Create an empty plan at the specified path.

#### Arguments

- `path` (FILE, required): The location in which to write a new `.plan.json` file. Must not exist.

### `reset`

Reset the progress on a plan file so it can be run again from scratch.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file

### `run`

Execute a plan file and then summarize it.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file

### `schema`

Tools to programmatically access the plan schema.

It includes the following subcommands:

- `url`
- `dump`

### `schema url`

Print the versioned url of Potent's JSON schema. Useful for getting in-editor completions or performing external validations.

### `schema dump`

Dump the current. While the versioned url is simpler to use, this schema will include any plugins you have, making it more complete & accurate for your use case.

#### Arguments

- `path` (FILE, required):

### `status`

Summarize the current state of a plan file. Also validates the file for schema issues.

#### Arguments

- `path` (FILE, required): The location of a `.plan.json` file

<!-- END:CLI -->

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
'direct...', 'allow_empty': True}}, input_type=dict]
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
