from pathlib import Path
from typing import Annotated, Optional, TextIO, Union

from annotated_types import Len
from pydantic import BaseModel, Field

from shellprints.directives._base import AbsPathList
from shellprints.directives.clean_workdir import CleanWorkdir
from shellprints.directives.git_pull import GitPull
from shellprints.directives.use_branch import UseBranch


class Shellprint(BaseModel):
    comment: Optional[str] = None
    steps: list[
        Annotated[
            Union[GitPull, UseBranch, CleanWorkdir],
            Field(discriminator="slug"),
        ]
    ]
    directories: Annotated[
        AbsPathList,
        Len(min_length=1),
    ]

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
