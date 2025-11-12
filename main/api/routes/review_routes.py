"""Deprecated Flask blueprint for review endpoints.

New implementation is provided by ``BGLApp_Refactor.api.routes.review``.
"""

from BGLApp_Refactor.api.routes.review import router  # type: ignore

bp = None

__all__ = ["router", "bp"]
