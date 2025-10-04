from typing import Literal

from shellprints.directives._base import BaseDirective


class GitPull(BaseDirective):
    slug: Literal["git-pull"]
