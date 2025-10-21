from pathlib import Path
from typing import Annotated, Literal, Optional, TextIO, Union

from annotated_types import Len
from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from rich.console import Group
from rich.tree import Tree

from potent.directives._base import AbsDirPath
from potent.directives.clean_workdir import CleanWorkdir
from potent.directives.create_pr import CreatePR
from potent.directives.enable_automerge import EnableAutomerge
from potent.directives.git_add import GitAdd
from potent.directives.git_commit import GitCommit
from potent.directives.git_pull import GitPull
from potent.directives.git_push import GitPush
from potent.directives.raw_command import RawCommand
from potent.directives.switch_branch import SwitchBranch

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
    steps: list[
        Annotated[
            Union[
                GitPull,
                SwitchBranch,
                CleanWorkdir,
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
        Len(min_length=1),
        AfterValidator(unique_items),
    ]
    _path: Optional[Path] = None

    @staticmethod
    def from_file(f: TextIO) -> "Plan":
        return Plan.model_validate_json(f.read())

    @staticmethod
    def from_path(f: Path) -> "Plan":
        plan = Plan.model_validate_json(f.read_text())
        plan._path = f
        return plan

    # def run(self):
    #     if not self._path:
    #         raise ValueError("Can't run plan without path")

    #     with self._path.open("r+") as fp:
    #         pass

    def save(self, f: TextIO):
        """
        Operates on an open file for performance reasons
        """
        f.seek(0)
        f.truncate()
        f.write(self.model_dump_json(indent=2))
        f.flush()

    def reset(self):
        for p in self.steps:
            p.reset()

    def render(self) -> Group:
        """
        Outputs a task tree suitable for Rich to show progress (w/ spinners)
        """
        raise NotImplementedError

    def directory_complete(self, directory: Path) -> bool:
        return all(s.completed(directory) for s in self.steps)

    def directory_failed(self, directory: Path) -> bool:
        return any(s.failed(directory) for s in self.steps)

    def directory_pending(self, directory: Path) -> bool:
        return all(s.pending(directory) for s in self.steps)

    def summarize(self, path: Path, *, short_plan=False) -> Tree:
        """
        Show this plan as plaintext
        """

        root = Tree(f"[yellow] {path.name if short_plan else path.absolute()}")
        # only print all steps if nothing has printed them yet
        should_print_all = True

        for d in self.directories:
            # res.append("")
            if self.directory_complete(d):
                root.add(f"✅ {d.name}", style="green", guide_style="green")

            elif self.directory_failed(d):
                should_print_all = False
                failed = root.add(f"❌ {d.name}", style="red", guide_style="red")
                for s in self.steps:
                    if s.completed(d):
                        failed.add(f"✅ {s.slug}", style="green")
                    elif s.failed(d):
                        failed.add(f"❌ {s.slug}", style="bold red")
                    else:
                        failed.add(f"⌛ {s.slug}", style="dim white")
            elif self.directory_pending(d):
                pending = root.add(f"⌛ {d.name}", style="yellow")
                if should_print_all:
                    should_print_all = False
                    for s in self.steps:
                        pending.add(f"⌛ {s.slug}", style="dim white")
                else:
                    pending.add("same steps as above", style="dim white")
            else:
                # plan was modified or something, so a previously-complete plan could now be incomplete
                pending = root.add(f"⌛ {d.name}", style="yellow")
                for s in self.steps:
                    if s.completed(d):
                        pending.add(f"✅ {s.slug}", style="green")
                    elif s.failed(d):
                        pending.add(f"❌ {s.slug}", style="red")
                    else:
                        pending.add(f"⌛ {s.slug}", style="bold white")

        return root
