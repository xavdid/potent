from typing import Literal, Optional

from shellprints.directives._base import BaseDirective


class UseBranch(BaseDirective):
    """
    Creates a branch if missing. Re-verifies you're on that branch every time
    """

    slug: Literal["git-checkout"]
    branch: str
    """
    branch name
    """
    # base: Optional[str]
    # """
    # Branch to base the new branch off of. Will switch to this first to create the branch.
    # """
