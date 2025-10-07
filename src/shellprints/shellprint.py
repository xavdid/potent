from pathlib import Path
from typing import Annotated, Any, Optional, TextIO, Union

from annotated_types import Len
from pydantic import AfterValidator, BaseModel, Field
from rich.console import Group

from shellprints.directives._base import AbsPath
from shellprints.directives.clean_workdir import CleanWorkdir
from shellprints.directives.git_pull import GitPull
from shellprints.directives.use_branch import UseBranch


def unique_items(v):
    if len(v) != len(set(v)):
        raise ValueError("list is not unique")
    return v


class Shellprint(BaseModel):
    comment: Optional[str] = None
    steps: list[
        Annotated[
            Union[GitPull, UseBranch, CleanWorkdir],
            Field(discriminator="slug"),
        ]
    ]
    directories: Annotated[
        list[AbsPath],
        Len(min_length=1),
        AfterValidator(unique_items),
    ]

    # def model_post_init(self, _) -> None:
    #     for s in self.steps:
    #         s.initialize_dirs(self.directories)

    @staticmethod
    def from_file(f: TextIO) -> "Shellprint":
        return Shellprint.model_validate_json(f.read())

    @staticmethod
    def from_path(f: Path) -> "Shellprint":
        return Shellprint.model_validate_json(f.read_text())

    def run(self):
        pass

    def save(self, f: TextIO):
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

    def summarize(self) -> str:
        """
        Show this plan as plaintext
        """

        res = []

        for d in self.directories:
            res.append("")
            if self.directory_complete(d):
                res.append(f"✅ {d.name}")
            elif self.directory_failed(d):
                res.append(f"❌ {d.name}:\n")
                for s in self.steps:
                    if s.completed(d):
                        res.append(f"  ✅ {s.slug}")
                    elif s.failed(d):
                        res.append(f"  ❌ {s.slug}")
                    else:
                        res.append(f"  ⌛ {s.slug}")
            else:
                res.append(f"⌛ {d.name}")

        res.append("")

        return "\n".join(res)
