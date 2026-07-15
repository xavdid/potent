from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from rich.console import Console
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
from potent.renderers import NoopRenderer, Renderer
from potent.run_events import (
    DirectorySkipped,
    DirectoryStarted,
    OperationCompleted,
)

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


def status_styling(s: Status, changed_this_run: bool) -> tuple[str, str, str, str]:
    """
    returns (emoji, title_style, text_style, guide_style)
    """
    match s, changed_this_run:
        case "completed", True:
            return "✅", "green", "green", "green"
        case "completed", False:
            return "☑️", "green", "green", "green"
        case "not-started", _:
            return "⏳", "yellow", "dim white", "dim white"
        case "failed", _:
            return "❌", "red", "red", "red"

    raise NotImplementedError


@dataclass
class OperationStatus:
    status: Status
    details: str
    """
    printed inline, after the emoji. Probably the result of `op.summary()`
    """
    completed_this_run: bool = False

    def to_tree(self) -> tuple[str, str | None]:
        emoji, _, text_color, _ = status_styling(self.status, self.completed_this_run)
        return (f"{emoji} {self.details}", text_color)


@dataclass
class DirectoryStatus:
    """
    A directory has a status and some number of child operations (all of which get printed)
    """

    name: Path
    status: Status
    op_results: list[OperationStatus]
    """
    the steps that should be printed. Some results omit this for brevity
    """
    completed_this_run: bool = False

    def add_to_tree(self, tree: Tree):
        emoji, title_color, _, guide_style = status_styling(
            self.status, self.completed_this_run
        )
        folder = tree.add(
            f"{emoji} {self.name.name}", style=title_color, guide_style=guide_style
        )

        for o in self.op_results:
            text, text_color = o.to_tree()
            folder.add(text, style=text_color)


@dataclass
class PlanStatus:
    """
    Visual representation of the state of a plan, maybe with additional information about the run that generated it.
    """

    filename: str
    directories: list[DirectoryStatus]
    includes_run_info: bool = False
    """
    Whether to include emoji that are part of a run
    """

    def to_tree(self) -> Tree:
        root = Tree(f"[yellow]{self.filename}")
        for d in self.directories:
            d.add_to_tree(root)

        return root

    def legend(self) -> str:
        return f"\n☑️ Completed{' | ✅ Completed this run' if self.includes_run_info else ''} | ⌛ Pending | ❌ Failed\n"


def directory_header(console: Console, directory: Path) -> None:
    return console.rule(
        f"📂 [bold underline]{directory.name}[/] 📂", style="bright_cyan"
    )


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
    _path: Optional[Path] = None
    """
    When running the plan, progress events are sent to the renderer for presentation
    """

    @staticmethod
    def from_path(path: Path) -> "Plan":
        plan = Plan.model_validate_json(path.read_text())
        plan._path = path
        return plan

    def save(self, path: Optional[Path] = None):
        """
        Persist an open Plan to disk. Errors if no path is provided _and_ the plan was not given a path at creation time.
        """

        dest = path or self._path

        if dest is None:
            raise ValueError("Can't save a Plan without a path.")

        tmp = dest.with_suffix(".tmp")
        # theoretically, writing the file can fail partway and leave us in a weird state
        tmp.write_text(self.model_dump_json(indent=2))
        # but the replace operation is atomic- if we get this far, the original write worked and we're ~guaranteed to produce a
        # this move retains the original file's metadata and deletes the tmp file in one go
        tmp.replace(dest)

        if path and (self._path is None):
            self._path = path

    def reset(self):
        for p in self.operations:
            p.reset()

    def directory_complete(self, directory: Path) -> bool:
        return all(s.completed(directory) for s in self.operations)

    def directory_failed(self, directory: Path) -> bool:
        return any(s.failed(directory) for s in self.operations)

    def directory_pending(self, directory: Path) -> bool:
        return any(s.pending(directory) for s in self.operations)

    def outline(self) -> Tree:
        """
        Show this plan's step as plaintext. Doesn't show status information, just an overview of the whole plan.
        """
        root = Tree(f"[yellow]{self._path.absolute() if self._path else ':in-memory:'}")

        if self.comment:
            info_leaf = root.add("summary", style="bold")
            info_leaf.add(self.comment, style="not bold")

        steps_leaf = root.add("operations:", style="bold")

        for op in self.operations:
            op_leaf = steps_leaf.add(op.summary, style="not bold")
            if op.comment:
                # manual confirmations have their comment in their summary
                op_leaf.add(op.comment)

        dir_leaf = root.add("directories:", style="bold")

        if self.directories:
            for d in self.directories:
                dir_leaf.add(str(d), style="not bold")
        else:
            dir_leaf.add("⚠️ none!", style="not bold yellow")

        return root

    def status(
        self,
        *,
        short_path=False,
        just_completed_steps: Optional[list[tuple[int, Path]]] = None,
    ) -> PlanStatus:
        """
        Show this plan as plaintext. Takes a path to print the plan's location, but not for actual file operations
        """

        if just_completed_steps is None:
            just_completed_steps = []

        # store what we _just_ finished, if anything
        completed_dirs = {p for _, p in just_completed_steps}

        if self._path:
            filename = self._path.name if short_path else str(self._path.absolute())
        else:
            filename = ":in memory:"

        result = PlanStatus(
            filename=filename,
            directories=[],
            includes_run_info=bool(just_completed_steps),
        )

        should_print_all = True
        for d in self.directories:
            status: Status = "not-started"
            operations = [
                OperationStatus(
                    status=o.dir_status(d),
                    completed_this_run=(idx, d) in just_completed_steps,
                    details=o.summary,
                )
                for idx, o in enumerate(self.operations)
            ]
            dir_completed_this_run = False

            if self.directory_complete(d):
                status = "completed"
                if not (dir_completed_this_run := d in completed_dirs):
                    operations = []

            elif self.directory_failed(d):
                status = "failed"
                # failures print all steps, so once we hit one, we no longer need to print every step
                should_print_all = False

            elif self.directory_pending(d):
                if should_print_all:
                    should_print_all = False
                else:
                    operations = []

            else:
                raise ValueError("Unknown status?")

            result.directories.append(
                DirectoryStatus(
                    name=d,
                    status=status,
                    op_results=operations,
                    completed_this_run=dir_completed_this_run,
                )
            )

        return result

    def run(
        self,
        skip_reset=False,
        renderer: Renderer = NoopRenderer(),
    ) -> PlanStatus:
        worked_dirs = []
        just_completed_steps: list[tuple[int, Path]] = []

        if self.config.mode == "command":
            if skip_reset:
                pass
            elif self.config.last_run != (today := date.today()):
                if self.config.last_run is not None:
                    renderer.log("Resetting plan")
                self.reset()
                self.config.last_run = today
        elif self.config.mode == "plan" and skip_reset:
            renderer.log(
                "[magenta]WARN: [bold cyan]--skip-reset[/] has no effect on non-command plans; ignoring.[/]"
            )

        for directory in self.directories:
            renderer.send(DirectoryStarted(directory))
            if self.directory_complete(directory):
                renderer.send(DirectorySkipped(directory))
                continue

            try:
                worked_dirs.append(directory)

                for idx, step in enumerate(self.operations):
                    success = None  # the ol' triple bool
                    ev = OperationCompleted(
                        directory, summary=step.summary, result="failure", output=""
                    )
                    if step.completed(directory):
                        ev.result = "skipped"
                        ev.output = "Already completed"
                    else:
                        result = step.run(directory)
                        if self._path:
                            self.save()
                        if success := result.success:
                            ev.result = "success"
                            just_completed_steps.append((idx, directory))

                        ev.output = result.output
                        ev.cmd = result.cmd

                    renderer.send(ev)

                    if success is False:
                        break

            except NotImplementedError:
                print("    err!")
                continue

        return self.status(
            short_path=True,
            just_completed_steps=just_completed_steps,
        )
