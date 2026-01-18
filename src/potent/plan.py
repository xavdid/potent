from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Literal, Optional, TextIO, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from rich.console import Group
from rich.tree import Tree

from potent.operations._base import AbsDirPath
from potent.operations.create_pr import CreatePR
from potent.operations.enable_automerge import EnableAutomerge
from potent.operations.git_add import GitAdd
from potent.operations.git_commit import GitCommit
from potent.operations.git_pull import GitPull
from potent.operations.git_push import GitPush
from potent.operations.git_status import GitStatus
from potent.operations.git_switch import GitSwitch
from potent.operations.raw_command import RawCommand

# DIRECTIVE IMPORTS ^


def unique_items(v):
    if len(v) != len(set(v)):
        raise ValueError("list is not unique")
    return v


Version = Literal["v1"]


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Version = "v1"
    comment: Optional[str] = None
    operations: list[
        Annotated[
            Union[
                GitPull,
                GitSwitch,
                GitStatus,
                GitAdd,
                GitCommit,
                GitPush,
                CreatePR,
                EnableAutomerge,
                RawCommand,
                # DIRECTIVES ^
            ],
            Field(discriminator="slug"),
        ]
    ]
    directories: Annotated[
        list[AbsDirPath],
        # Len(min_length=1), # we don't want to init plans with a directory that may not exist (or does exist, but has important things in it)
        AfterValidator(unique_items),
    ]
    _fp: Optional[TextIO] = None

    @staticmethod
    @contextmanager
    def open(path: Path):
        """
        Open a plan at `path` for reading & writing. Stores the pointer on the plan.
        """
        with path.open("r+") as fp:
            plan = Plan.model_validate_json(fp.read())
            plan._fp = fp
            try:
                yield plan
            finally:
                plan._fp = None

    @staticmethod
    def from_path(f: Path) -> "Plan":
        return Plan.model_validate_json(f.read_text())

    def save(self):
        """
        Operates on an open file for performance reasons
        """
        if self._fp is None:
            raise ValueError("Can't do file operations without a file pointer")

        self._fp.seek(0)
        self._fp.truncate()
        self._fp.write(self.model_dump_json(indent=2))
        self._fp.flush()

    def reset(self):
        for p in self.operations:
            p.reset()

    def directory_complete(self, directory: Path) -> bool:
        return all(s.completed(directory) for s in self.operations)

    def directory_failed(self, directory: Path) -> bool:
        return any(s.failed(directory) for s in self.operations)

    def directory_pending(self, directory: Path) -> bool:
        return all(s.pending(directory) for s in self.operations)

    def summarize(
        self,
        path: Path,
        *,
        short_plan=False,
        verbose_success_dirs: Optional[list[Path]] = None,
        current_run: Optional[list[tuple[Path, str]]] = None,
    ) -> Tree:
        """
        Show this plan as plaintext. Takes a path to print the plan's location, but not for actual file operations
        """
        # TODO: this is a mess
        if verbose_success_dirs is None:
            verbose_success_dirs = []
        if current_run is None:
            current_run = []

        if verbose_success_dirs or current_run:
            print("☑️ Completed | ✅ Completed this run | ⌛ Pending | ❌ Failed\n")
        else:
            print("☑️ Completed | ⌛ Pending | ❌ Failed\n")

        root = Tree(f"[yellow]{path.name if short_plan else path.absolute()}")
        # only print all steps if nothing has printed them yet
        should_print_all = True
        for d in self.directories:
            if self.directory_complete(d):
                emoji = (
                    "✅" if any(directory == d for directory, _ in current_run) else "☑️"
                )
                completed = root.add(
                    f"{emoji} {d.name}", style="green", guide_style="green"
                )
                if d in verbose_success_dirs:
                    for s in self.operations:
                        step_emoji = "✅" if (d, s.slug) in current_run else "☑️"
                        completed.add(f"{step_emoji} {s.slug}", style="green")

            elif self.directory_failed(d):
                should_print_all = False
                failed = root.add(f"❌ {d.name}", style="red", guide_style="red")
                for s in self.operations:
                    if s.completed(d):
                        succeded_this_run = (d, s.slug) in current_run
                        step_emoji = "✅" if succeded_this_run else "☑️"
                        failed.add(
                            f"{step_emoji} {s.slug}",
                            style="green",
                        )
                    elif s.failed(d):
                        failed.add(f"❌ {s.slug}", style="bold red")
                    else:
                        failed.add(f"⌛ {s.slug}", style="dim white")
            elif self.directory_pending(d):
                pending = root.add(f"⌛ {d.name}", style="yellow")
                if should_print_all:
                    should_print_all = False
                    for s in self.operations:
                        pending.add(f"⌛ {s.slug}", style="dim white")
                else:
                    pending.add("same steps as above", style="dim white")
            else:
                # plan was modified or something, so a previously-complete plan could now be incomplete
                pending = root.add(f"⌛ {d.name}", style="yellow")
                for s in self.operations:
                    if s.completed(d):
                        pending.add(f"☑️ {s.slug}", style="green")
                    elif s.failed(d):
                        pending.add(f"❌ {s.slug}", style="red")
                    else:
                        pending.add(f"⌛ {s.slug}", style="bold white")

        return root
