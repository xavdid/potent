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
│   ├── ✅ clean-status
│   ├── ✅ switch-branch
│   ├── ✅ git-commit
│   └── ✅ git-push
├── ❌ badger
│   ├── ❌ clean-status
│   ├── ⌛ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ✅ clean-status
    ├── ❌ switch-branch
    ├── ⌛ git-commit
    └── ⌛ git-push
```

## Table of Contents

- [Install](#install)
- [Plans](#plans)
- [Directives](#directives)
- [FAQ](#faq)
- [Project Status](#project-status)
- [Demo](#demo)

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

Plans have two main components:

- a list of directories
- a list of steps

Each step is identified by its unique `slug` field.

### Authoring Plan files

Plans are just JSON, so you can write them by hand or generate them using other programs.

If you're handwriting, you can tell VSCode (or any other editor that supports JSON Schema) that `*.plan.json` files must match the schema by adding the following to your settings:

```json
"json.schemas": [
  {
    "fileMatch": ["*.plan.json"],
    "url": "https://raw.githubusercontent.com/xavdid/potent/refs/heads/main/schema.json"
  }
]
```

Using the schema will help with autocomplete and flag any potential errors.

## Directives

Each of the directives below describes a single operation with well-defined arguments. If you need more flexibility, check out the [raw command](#rawcommand) directive.

<!-- BEGIN:DIRECTIVES -->

### CreatePR

Creates a pull request using the `gh` CLI.

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

Enables automerge for the PR corresponding to the current branch.

**Slug**: `enable-automerge`

#### Config

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

Ensures that you have a clean working directory. If there are any modified or unstaged files, this step fails.

**Slug**: `git-status`

### GitSwitch

Switches the local git branch. Can optionally create it if it's missing.

**Slug**: `switch-branch`

#### Config

| name                | type   | description                                                 | default (if optional) |
| ------------------- | ------ | ----------------------------------------------------------- | --------------------- |
| `branch`            | `str`  | branch name                                                 |                       |
| `create_if_missing` | `bool` | If true, tries creating the branch if switching to it fails | `False`               |

### RawCommand

Runs a shell command. The step succeeds if the command exits 0 and fails otherwise.

**Slug**: `raw-command`

#### Config

| name        | type        | description                                                                                                                        | default (if optional) |
| ----------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `arguments` | `list[str]` | The arguments that will be passed into Python's [subprocess.run](https://docs.python.org/3/library/subprocess.html#subprocess.run) |                       |

<!-- END:DIRECTIVES -->

## FAQ

### Reading validation messages

The error you get when you have an invalid plan file can take a little getting used to. TKTK.

## Project Status

`potent` is still under active development. Before we reach `1.0.0`, there may be breaking changes to existing schemas in any release.

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
  "steps": [
    {
      "slug": "clean-status"
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
│   ├── ⌛ clean-status
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
╭─ step: clean-status ─────────────────────────────────────────────────────╮
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
╭─ step: clean-status ─────────────────────────────────────────────────────╮
│                                                                          │
│ >>> git status --porcelain                                               │
│                                                                          │
│ fatal: not a git repository (or any of the parent directories): .git     │
│                                                                          │
╰─ result: Failed ─────────────────────────────────────────────────────────╯


─────────────────────────────── 📂 camel 📂 ────────────────────────────────
╭─ step: clean-status ─────────────────────────────────────────────────────╮
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
│   ├── ✅ clean-status
│   ├── ✅ switch-branch
│   ├── ✅ git-commit
│   └── ✅ git-push
├── ❌ badger
│   ├── ❌ clean-status
│   ├── ⌛ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ✅ clean-status
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
╭─ step: clean-status ─────────────────────────────────────────────────────╮
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
╭─ step: clean-status ─────────────────────────────────────────────────────╮
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
│   ├── ✅ clean-status
│   ├── ❌ switch-branch
│   ├── ⌛ git-commit
│   └── ⌛ git-push
└── ❌ camel
    ├── ☑️ clean-status
    ├── ✅ switch-branch
    ├── ✅ git-commit
    └── ❌ git-push
```

The ✅ marks show what steps we completed this run, while ☑️ denotes a step we completed on a previous run.

`aardvark` was skipped since it was already done. We made progress in `badger` and `camel` despite erroring out because we can't switch branches without commits and there's nothing to push to.

But, I could resume my script from the middle, skipping any completed steps. This is the power of `potent`!
