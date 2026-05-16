from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Optional, TextIO, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from rich.tree import Tree

from potent.operations._base import AbsDirPath, Status
from potent.operations.create_pr import CreatePR
from potent.operations.enable_automerge import EnableAutomerge
from potent.operations.git_add import GitAdd
from potent.operations.git_commit import GitCommit
from potent.operations.git_pull import GitPull
from potent.operations.git_push import GitPush
from potent.operations.git_status import GitStatus
from potent.operations.git_switch import GitSwitch
from potent.operations.manual_confirmation import ManualConfirmation
from potent.operations.raw_command import RawCommand

# OPERATION IMPORTS ^


def unique_items(v):
    if len(v) != len(set(v)):
        raise ValueError("list is not unique")
    return v


Version = Literal["v1"]


class PlanConfig(BaseModel):
    """
    One of the configuration options for a Plan
    """

    mode: Literal["plan"] = "plan"
    """
    plans are run as one-off operations (that can be manually reset)
    """


class CommandConfig(BaseModel):
    """
    One of the configuration options for a Plan
    """

    mode: Literal["command"] = "command"
    """
    commands are auto-resetting plans
    """
    last_run: Optional[date] = None
    """
    the iso date (`YYYY-MM-DD`) on which this command was last run. If a command is run and `date.today()` doesn't match this value, the command is reset before proceeding. Otherwise, it runs as normal (maybe as a no-op). The plan can still be manually reset; this value only affects auto-resetting behavior.
    """


class OperationResult(BaseModel):
    status: Status
    details: str
    """
    printed inline, after the emoji
    """
    changed_this_run: bool = False


class DirectoryStatus(BaseModel):
    """
    A directory has a status and some number of child operations (all of which get printed)
    """

    name: Path
    status: Status
    operations: list[OperationResult]
    """
    whether all steps should be printed. True if it's the first directory or one of the steps had an error.
    """
    completed_this_run: bool = False


class PlanStatus(BaseModel):
    """
    Visual representation of a plan, maybe with additional information about the run that generated it.
    """

    filename: str
    directories: list[DirectoryStatus]

    def print(self):
        # print to a rich console
        raise NotImplementedError


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    config: Annotated[Union[PlanConfig, CommandConfig], Field(discriminator="mode")] = (
        PlanConfig()
    )

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
                ManualConfirmation,
                # OPERATIONS ^
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
        Persist an open Plan to disk.
        """
        if self._fp is None:
            raise ValueError(
                "Can't do file operations without a file pointer. Consider opening the Plan with the `.open` context manager."
            )

        self._fp.seek(0)
        self._fp.truncate()
        self._fp.write(self.model_dump_json(indent=2))
        # without this, files may not actually be written right away
        # but we want to store incremental progress as soon as possible in case something goes wrong
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

    def outline(self, path: Path) -> Tree:
        """
        Show this plan's step as plaintext. Doesn't show status information, just an overview of the whole plan.
        """
        root = Tree(f"[yellow]{path.absolute()}")

        if self.comment:
            info_leaf = root.add("summary", style="bold")
            info_leaf.add(self.comment, style="not bold")

        steps_leaf = root.add("operations:", style="bold")

        for op in self.operations:
            op_leaf = steps_leaf.add(op.summary, style="not bold")
            if op.comment:
                op_leaf.add(op.comment)

        dir_leaf = root.add("directories:", style="bold")

        for d in self.directories:
            dir_leaf.add(str(d), style="not bold")

        return root

    def status(
        self,
        # TODO: the plan should probably know this?? weird to pass it in
        path: Path,
        *,
        short_plan=False,
        verbose_success_dirs: Optional[list[Path]] = None,
        just_completed_steps: Optional[list[tuple[int, Path]]] = None,
    ) -> PlanStatus:
        """
        Show this plan as plaintext. Takes a path to print the plan's location, but not for actual file operations
        """
        # TODO: this is a mess
        if verbose_success_dirs is None:
            verbose_success_dirs = []
        if just_completed_steps is None:
            just_completed_steps = []

        if verbose_success_dirs or just_completed_steps:
            # do these always overlap?
            completed_paths = {p for _, p in just_completed_steps}
            assert completed_paths == set(verbose_success_dirs), (
                f"expeceted {completed_paths=} and {verbose_success_dirs=} to be equal?"
            )

        # TODO: remove/move
        if verbose_success_dirs or just_completed_steps:
            print("☑️ Completed | ✅ Completed this run | ⌛ Pending | ❌ Failed\n")
        else:
            print("☑️ Completed | ⌛ Pending | ❌ Failed\n")

        result = PlanStatus(
            filename=path.name if short_plan else str(path.absolute()),
            directories=[],
        )

        should_print_all = True
        for d in self.directories:
            status: Status = "not-started"
            operations: list[OperationResult] = []
            completed_this_run = False

            if self.directory_complete(d):
                completed_this_run = any(
                    directory == d for _, directory in just_completed_steps
                )
                # `verbose_success_dirs` is what we worked on this run. If we worked a directory and it's now complete, show all the steps
                if d in verbose_success_dirs:
                    operations = [
                        OperationResult(
                            status="completed",
                            changed_this_run=(idx, d) in just_completed_steps,
                            details=o.summary,
                        )
                        for idx, o in enumerate(self.operations)
                    ]

            elif self.directory_failed(d):
                status = "failed"
                # failures print all steps, so once we hit one, we no longer need to print every step
                should_print_all = False
                operations = [
                    OperationResult(
                        status=o.dir_status(d),
                        changed_this_run=(idx, d) in just_completed_steps,
                        details=o.summary,
                    )
                    for idx, o in enumerate(self.operations)
                ]

            elif self.directory_pending(d):
                status = "not-started"
                if should_print_all:
                    should_print_all = False
                    operations = [
                        OperationResult(
                            status="not-started",
                            details=o.summary,
                        )
                        for o in self.operations
                    ]

            else:
                # plan was modified or something, so a previously-complete plan could now be incomplete
                status = "not-started"
                operations = [
                    OperationResult(
                        status=o.dir_status(d),
                        details=o.summary,
                    )
                    for o in self.operations
                ]

            result.directories.append(
                DirectoryStatus(
                    name=d,
                    status=status,
                    operations=operations,
                    completed_this_run=completed_this_run,
                )
            )

        return result


# only print all steps if nothing has printed them yet
# should_print_all = True
# for d in self.directories:
#     if self.directory_complete(d):
#         emoji = (
#             # TODO: fix!
#             "✅" if any(directory == d for directory, _ in current_run) else "☑️"
#         )
#         completed = root.add(
#             f"{emoji} {d.name}", style="green", guide_style="green"
#         )
#         if d in verbose_success_dirs:
#             for s in self.operations:
#                 # TODO: fix!
#                 step_emoji = "✅" if (d, s.summary) in current_run else "☑️"
#                 completed.add(
#                     f"{step_emoji} {s.summary}",
#                     style="green",
#                 )

#     elif self.directory_failed(d):
#         should_print_all = False
#         failed = root.add(f"❌ {d.name}", style="red", guide_style="red")
#         for s in self.operations:
#             if s.completed(d):
#                 # TODO: fix!
#                 succeded_this_run = (d, s.summary) in current_run
#                 step_emoji = "✅" if succeded_this_run else "☑️"
#                 failed.add(
#                     f"{step_emoji} {s.summary}",
#                     style="green",
#                 )
#             elif s.failed(d):
#                 failed.add(f"❌ {s.summary}", style="bold red")
#             else:
#                 failed.add(f"⌛ {s.summary}", style="dim white")
#     elif self.directory_pending(d):
#         pending = root.add(f"⌛ {d.name}", style="yellow")
#         if should_print_all:
#             should_print_all = False
#             for s in self.operations:
#                 pending.add(f"⌛ {s.summary}", style="dim white")
#         else:
#             pending.add("same steps as above", style="dim white")
#     else:
#         # plan was modified or something, so a previously-complete plan could now be incomplete
#         pending = root.add(f"⌛ {d.name}", style="yellow")
#         for s in self.operations:
#             if s.completed(d):
#                 pending.add(f"☑️ {s.summary}", style="green")
#             elif s.failed(d):
#                 pending.add(f"❌ {s.summary}", style="red")
#             else:
#                 pending.add(f"⌛ {s.summary}", style="bold white")
