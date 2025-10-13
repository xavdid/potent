from pathlib import Path
from typing import Annotated, Literal, Optional, TextIO, Union

from annotated_types import Len
from pydantic import AfterValidator, BaseModel, Field
from rich.console import Group
from rich.tree import Tree

from potent.directives._base import AbsPath
from potent.directives.clean_workdir import CleanWorkdir
from potent.directives.git_add import GitAdd
from potent.directives.git_commit import GitCommit
from potent.directives.git_pull import GitPull
from potent.directives.git_push import GitPush
from potent.directives.switch_branch import SwitchBranch

# DIRECTIVE IMPORTS ^


def unique_items(v):
    if len(v) != len(set(v)):
        raise ValueError("list is not unique")
    return v


Version = Literal["v1"]


class Plan(BaseModel):
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
                # DIRECTIVES ^
            ],
            Field(discriminator="slug"),
        ]
    ]
    directories: Annotated[
        list[AbsPath],
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

    # def directory_started(self, directory: Path) -> bool:
    #     return any(s.completed(directory) for s in self.steps)

    def summarize(self, path: Path, *, short=False) -> Tree:
        """
        Show this plan as plaintext
        """

        root = Tree(f"[yellow] {path.name if short else path.absolute()}")
        # only print all steps if nothing has printed them yet
        should_print_all = True

        for d in self.directories:
            # res.append("")
            if self.directory_complete(d):
                root.add(f"✅ {d.name}", style="green", guide_style="green")

                # res.append(f"✅ {d.name}")
            elif self.directory_failed(d):
                should_print_all = False
                failed = root.add(f"❌ {d.name}", style="red", guide_style="red")
                # res.append(f"❌ {d.name}:\n")
                for s in self.steps:
                    if s.completed(d):
                        failed.add(f"✅ {s.slug}", style="green")
                        # res.append(f"  ✅ {s.slug}")
                    elif s.failed(d):
                        failed.add(f"❌ {s.slug}", style="red")
                        # res.append(f"  ❌ {s.slug}")
                    else:
                        failed.add(f"⌛ {s.slug}", style="dim white")
                        # res.append(f"  ⌛ {s.slug}")
            else:
                pending = root.add(f"⌛ {d.name}", style="yellow")
                if should_print_all:
                    should_print_all = False
                    for s in self.steps:
                        pending.add(f"{s.slug}", style="white")
                else:
                    pending.add("same as above", style="dim white")

                # res.append(f"⌛ {d.name}")

        # res.append("")

        # return "\n".join(res)
        return root
