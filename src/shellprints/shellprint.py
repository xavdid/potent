from typing import Annotated, Union

from annotated_types import Len
from pydantic import Field

from shellprints.directives._base import AbsPathList, BaseDirective
from shellprints.directives.clean_status import CleanStatus
from shellprints.directives.git_pull import GitPull
from shellprints.directives.use_branch import UseBranch


class Shellprint(BaseDirective):
    steps: list[
        Annotated[
            Union[GitPull, UseBranch, CleanStatus],
            Field(discriminator="slug"),
        ]
    ]
    directories: Annotated[
        AbsPathList,
        Len(min_length=1),
    ]

    def run(self):
        pass
