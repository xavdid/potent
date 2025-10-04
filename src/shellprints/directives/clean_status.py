from typing import Literal

from shellprints.directives._base import BaseDirective


class CleanStatus(BaseDirective):
    slug: Literal["clean-status"]
