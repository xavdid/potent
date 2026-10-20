import os.path
from dataclasses import dataclass
from datetime import date
from functools import partial
from pathlib import Path
from typing import (
    Annotated,
    ClassVar,
    Literal,
    Optional,
    Union,
    assert_never,
)

from pydantic import AfterValidator, BaseModel, Field
from rich.console import Console
from rich.tree import Tree

from potent.operations._base import (
    AbsDirPath,
    BaseOperation,
    CommonBase,
    Context,
    PrintableStatus,
)
from potent.operations.assert_branch import AssertBranch
from potent.operations.change_pr_status import ChangePrStatus
from potent.operations.create_pr import CreatePR
from potent.operations.enable_automerge import SetAutomerge
from potent.operations.git_add import GitAdd
from potent.operations.git_commit import GitCommit
from potent.operations.git_pull import GitPull
from potent.operations.git_push import GitPush
from potent.operations.git_status import GitStatus
from potent.operations.git_switch import GitSwitch
from potent.operations.manual_confirmation import ManualConfirmation
from potent.operations.raw_command import RawCommand
from potent.plugins import get_ops_from_plugins
from potent.renderers import NoopRenderer, Renderer
from potent.run_events import (
    DirectorySkipped,
    DirectoryStarted,
    OperationFinished,
    OperationStarted,
)
from potent.util import (
    DataReadException,
    DataValType,
    get_template_runs_dir,
    get_templates_dir,
)

# OPERATION IMPORTS ^

MANUAL_CONFIRMATION_SLUG = ManualConfirmation().slug
NUM_OLD_TEMPLATE_RUNS_KEPT = 15


def unique_items(v):
    if len(v) != len(set(v)):
        raise ValueError("list is not unique")
    return v


class PlanConfig(BaseModel):
    """
    One of the configuration options for a Plan
    """

    mode: Literal["plan"] = "plan"
    """
    plans are run as one-off operations (that can be manually reset)
    """


class TemplateConfig(BaseModel):
    """
    One of the configuration options for a Plan
    """

    mode: Literal["template"] = "template"
    """
    plans are run as one-off operations (that can be manually reset)
    """


def status_styling(
    s: PrintableStatus, changed_this_run: bool
) -> tuple[str, str, str, str]:
    """
    returns (emoji, title_style, text_style, guide_style)
    """
    match s, changed_this_run:
        case "completed", True:
            return "✅", "green", "green", "green"
        case "completed", False:
            return "☑️", "green", "green", "green"
        case "not-started", _:
            return "⏳", "white", "dim white", "dim white"
        case "duplicate", _:
            return "♊", "white", "white", "dim white"
        case "failed", _:
            return "❌", "red", "red", "red"
        case "halted", _:
            return "⏸️", "yellow", "yellow", "yellow"
        case n:
            assert_never(n)

    raise NotImplementedError


@dataclass(eq=True)
class OperationStatus:
    status: PrintableStatus
    op_slug: str
    """
    Operation slug, so it's identifiable later. Not typechecked, since Python has no mapped types
    """
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

    path: Path
    status: PrintableStatus
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
            f"{emoji} {self.path.name}", style=title_color, guide_style=guide_style
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
    Whether to include emoji in the legend to mark items that were completed this run
    """

    def to_tree(self) -> Tree:
        root = Tree(f"[yellow]{self.filename}")
        for d in self.directories:
            d.add_to_tree(root)

        return root

    def legend(self) -> str:
        return f"\n☑️ Completed{' | ✅ Completed this run' if self.includes_run_info else ''} | ⏸️ Needs confirmation | ⌛ Pending | ❌ Failed\n"


def directory_header(console: Console, directory: Path) -> None:
    return console.rule(
        f"📂 [bold underline]{directory.name}[/] 📂", style="bright_cyan"
    )


# declaring this here instead of as an annotation means it can be built at runtime
Operations = list[
    Annotated[
        Union[
            GitPull,
            GitSwitch,
            GitStatus,
            GitAdd,
            GitCommit,
            GitPush,
            CreatePR,
            SetAutomerge,
            RawCommand,
            ManualConfirmation,
            ChangePrStatus,
            AssertBranch,
            # OPERATIONS ^
            *get_ops_from_plugins(),
        ],
        Field(discriminator="slug"),
    ]
]


class Plan(CommonBase):
    config: Annotated[PlanConfig | TemplateConfig, Field(discriminator="mode")] = (
        PlanConfig()
    )

    version: Literal["v1"] = "v1"
    comment: Optional[str] = None
    operations: Operations
    directories: Annotated[
        list[AbsDirPath],
        # Len(min_length=1), # we don't want to init plans with a directory that may not exist (or does exist, but has important things in it)
        AfterValidator(unique_items),
    ]
    data: Optional[dict[str, dict[str, DataValType]]] = None
    _path: Optional[Path] = None
    """
    When running the plan, progress events are sent to the renderer for presentation
    """

    ignored_fields_for_compare: ClassVar[set[str]] = {"config", "comment", "data"}

    @staticmethod
    def from_path(path: Path) -> "Plan":
        plan = Plan.model_validate_json(path.read_text())
        plan._path = path
        return plan

    def save(self, path: Optional[Path] = None):
        """
        Persist an open Plan to disk. Errors if no path is provided _and_ the plan was not given a path at creation time.
        """

        if (dest := path or self._path) is None:
            raise ValueError("Can't save a Plan without a path.")

        tmp = dest.with_suffix(".tmp")
        # theoretically, writing the file can fail partway and leave us in a weird state
        tmp.write_text(self.model_dump_json(indent=2, exclude_none=True))
        # but the replace operation is atomic- if we get this far, the original write worked and we're ~guaranteed to produce a
        # this move retains the original file's metadata and deletes the tmp file in one go
        tmp.replace(dest)

        if self._path is None:
            self._path = path

    def reset(self):
        for p in self.operations:
            p.reset()
        self.data = None

    def directory_complete(self, directory: Path) -> bool:
        return all(o.is_completed(directory) for o in self.operations)

    def directory_failed(self, directory: Path) -> bool:
        return any(o.is_failed(directory) for o in self.operations)

    def directory_pending(self, directory: Path) -> bool:
        """
        if the first incomplete step is a manual-confirmation
        """
        for o in self.operations:
            if o.is_completed(directory):
                continue

            # if the first non-complete step is a pending one, then the directory is also pending
            return o.is_pending(directory)

        # if we never returned above, must not be halted
        return False

    def directory_halted(self, directory: Path) -> bool:
        """
        if the first incomplete step is a manual-confirmation
        """
        for o in self.operations:
            if o.is_completed(directory):
                continue

            # if we hit a manual confirmation that isn't completed, the step is halted
            if o.slug == MANUAL_CONFIRMATION_SLUG:
                return True

            # any other incomplete step is a failure or a pending, so it's not halted
            # fall back to the outer return
            break

        # if we never returned above, must not be halted
        return False

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

    def plan_name(self, short_path=False) -> str:
        if self._path:
            return self._path.name if short_path else str(self._path.absolute())

        return ":in memory:"

    def status(
        self,
        *,
        short_path=False,
        collapse_duplicates=False,
        just_completed_steps: Optional[list[tuple[int, Path]]] = None,
    ) -> PlanStatus:
        """
        Show this plan as plaintext.
        """

        if just_completed_steps is None:
            just_completed_steps = []

        # store what we _just_ finished, if anything
        completed_dirs = {p for _, p in just_completed_steps}

        result = PlanStatus(
            filename=self.plan_name(short_path),
            directories=[],
            includes_run_info=bool(just_completed_steps),
        )

        seen: dict[Path, list[OperationStatus]] = {}
        for d in self.directories:
            status: PrintableStatus = "not-started"
            operation_statuses = [
                OperationStatus(
                    status=o.dir_status(d),
                    op_slug=o.slug,
                    completed_this_run=(idx, d) in just_completed_steps,
                    details=self.resolve_operation(
                        o, d, raise_read_errors=False
                    ).summary,
                )
                for idx, o in enumerate(self.operations)
            ]
            dir_completed_this_run = False

            if self.directory_complete(d):
                status = "completed"
                if not (dir_completed_this_run := d in completed_dirs):
                    operation_statuses = []

            elif self.directory_halted(d):
                status = "halted"

                # mark the halted status that's are actually holding up the step
                for o in operation_statuses:
                    if (
                        o.op_slug == MANUAL_CONFIRMATION_SLUG
                        and o.status != "completed"
                    ):
                        o.status = "halted"
                        break

            elif self.directory_pending(d):
                # already use the default status
                # but need this block so we don't hit a different case
                pass

            elif self.directory_failed(d):
                status = "failed"

            else:
                raise ValueError("Unknown status?")

            # if the directory isn't complete and our manual step isn't otherwise marked, don't mark it as failed
            if status in {"not-started", "failed"}:
                for o in operation_statuses:
                    if (
                        o.op_slug == MANUAL_CONFIRMATION_SLUG
                        and o.status != "completed"
                    ):
                        o.status = "not-started"

            # don't treat empty lists as dupes
            if collapse_duplicates and operation_statuses:
                for seen_path, seen_ops in seen.items():
                    # it might be nice to deduplicate these? like
                    # a, b, c
                    # \
                    #  - complete
                    #  - complete

                    # instead of:

                    # a
                    # \
                    #  - complete
                    #  - complete
                    # b: same as a
                    # c: same as a

                    # but that requires doing a check here that modifies how the `result.directories` is build.
                    # `DirectoryStatus` assumes a `Path`, so there's a bunch to unwind if we do that
                    if operation_statuses == seen_ops:
                        operation_statuses = [
                            OperationStatus(
                                status="duplicate",
                                op_slug="duplicate",  # doesn't matter; only ever needed for manual conf
                                details=f"Same as `[bold cyan]{seen_path.name}[/]`",
                            )
                        ]
                        break
                seen[d] = operation_statuses

            result.directories.append(
                DirectoryStatus(
                    path=d,
                    status=status,
                    op_results=operation_statuses,
                    completed_this_run=dir_completed_this_run,
                )
            )

        return result

    def run(self, renderer: Renderer = NoopRenderer()) -> list[tuple[int, Path]]:
        """
        Executes a plan, modifying this object. Returns the steps that it completed this run
        """
        if self.config.mode == "template":
            raise ValueError("Can't run template-type plans.")

        worked_dirs = []
        just_completed_steps: list[tuple[int, Path]] = []

        for directory in self.directories:
            renderer.send(DirectoryStarted(directory))
            if self.directory_complete(directory):
                renderer.send(DirectorySkipped(directory))
                continue

            worked_dirs.append(directory)

            for idx, step in enumerate(self.operations):
                success: Optional[bool] = None  # the ol' triple bool
                ev = OperationFinished(
                    directory, summary=step.summary, result="failure", output=""
                )

                if not step.always_rerun and step.is_completed(directory):
                    ev.result = "skipped"
                    ev.output = "Already completed"
                else:
                    renderer.send(
                        OperationStarted(
                            path=directory,
                            summary=self.resolve_operation(
                                step, directory, raise_read_errors=False
                            ).summary,
                        )
                    )

                    try:
                        resolved_step = self.resolve_operation(step, directory)
                    except DataReadException as e:
                        ev.output = f"Unexpected data read error: {e!s}"
                        step.record_result(directory, False)
                    else:
                        result = resolved_step.run_and_record_result(
                            raw_directory=directory,
                            context=Context(
                                # we know the path exists, but it may need to be expanded before use
                                directory=directory.expanduser(),
                                _read_func=partial(self.read_data, directory),
                                _write_func=partial(self.write_data, directory),
                            ),
                        )
                        if self._path:
                            self.save()

                        if success := result.success:
                            ev.result = "success"
                            # don't log asserts as new every time
                            if not step.always_rerun:
                                just_completed_steps.append((idx, directory))
                        elif step.slug == MANUAL_CONFIRMATION_SLUG:
                            # it failed, but mark it as halted instead of failed
                            ev.result = "halted"

                        ev.output = result.output
                        ev.cmd = result.cmd

                renderer.send(ev)

                if success is False:
                    break

        return just_completed_steps

    def resolve_operation[T: BaseOperation](
        self,
        op: T,
        directory: Path,
        *,
        raise_read_errors: bool = True,
    ) -> T:
        """
        Given an operation (which includes any configuration data) & a directory, attempt to resolve all variables in the config with their corresponding data entries. Returns the resolved copy of the operation (or the original if it has no variables to replace).
        """

        def lookup(key: str) -> DataValType:
            try:
                return self.read_data(directory, key)
            except DataReadException:
                if raise_read_errors:
                    raise
                return f"{{{{ {key} }}}}"  # leave the template visible

        return op._resolve(lookup)

    def read_data(self, directory: Path, key: str) -> DataValType:
        """
        Read `key` for this `directory` from the plan's `data` dict.

        Raises `DataReadException` if any intermediate structures are missing.
        """
        directory_str = str(directory)
        if self.data is None:
            raise DataReadException("no data has been written")

        if self.data.get(directory_str) is None:
            raise DataReadException("no data has been written for this directory")

        try:
            return self.data[directory_str][key]
        except KeyError:
            raise DataReadException(
                f'Key "{key}" was not present in data for "{directory_str}"'
            )

    def write_data(self, directory: Path, key: str, value: DataValType) -> None:
        """
        Write `key`:`value` for this `directory` into the plan's `data` dict, creating intermediate structures as needed.
        """
        directory_str = str(directory)
        if self.data is None:
            self.data = {}

        if self.data.get(directory_str) is None:
            self.data[directory_str] = {}

        self.data[directory_str][key] = value

    def convert_template(self) -> "Plan":
        """
        If a plan is a template, copy it to the template dir as a real plan w/ an escaped path pointing to the original
        """
        if self.config.mode == "plan":
            return self
        if self.config.mode == "template":
            if not self._path:
                raise ValueError("expected template plan to have a _path")
            dest_path = get_template_runs_dir() / self.template_dest_path()

            if dest_path.exists():
                copied_plan = Plan.from_path(dest_path)

                if copied_plan.dump_for_comparison() != self.dump_for_comparison():
                    raise ValueError(
                        f"Cannot safely run because the copied plan ({str(dest_path)}) has diverged from its template. To proceed, either delete the copied plan and re-run the template or run the copied plan directly."
                    )

                return copied_plan

            dest_path.parent.mkdir(exist_ok=True, parents=True)

            plan = self.model_copy(
                update={"config": PlanConfig(), "_path": dest_path},
                # it's as if we reloaded everything from disk
                deep=True,
            )
            plan.save()
            return plan

        assert_never(self.config.mode)

    def clean_old_template_runs(self):
        if self.config.mode != "template":
            raise ValueError("Can only clean template runs from a template")

        if not self._path:
            raise ValueError("Can only clean template if the template has a path")

        stem = escape_path(self._path).name

        existing_runs = sorted(
            p for p in get_template_runs_dir().iterdir() if p.name.endswith(stem)
        )

        # delete matching files until we only have NUM_OLD_TEMPLATE_RUNS_KEPT remaining
        # if the number of files is smaller than the length of the list, this is empty
        for p in existing_runs[:-NUM_OLD_TEMPLATE_RUNS_KEPT]:
            p.unlink()

    def template_dest_path(self) -> Path:
        """
        Where a copied template should be written
        """

        if not self._path:
            raise ValueError("Can't compute dest path without a _path")

        return Path(f"{date.today()}_{escape_path(self._path)}")


def get_plans_from_path(path: Path) -> list[Plan]:
    return [
        Plan.from_path(p) for p in path.iterdir() if p.suffixes == [".plan", ".json"]
    ]


def get_available_templates() -> tuple[list[Plan], list[Plan]]:
    return get_plans_from_path(get_templates_dir()), get_plans_from_path(Path.cwd())


def escape_path(path: Path) -> Path:
    """
    Given a path, escape it so it can be used in another path
    """

    return Path(str(path).replace("|", "||").replace(os.path.sep, "|"))
