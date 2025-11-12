"""Deprecated Flask blueprint kept for legacy code.

Use ``BGLApp_Refactor.api.routes.aliases`` instead.
"""

from BGLApp_Refactor.api.routes.aliases import router  # type: ignore

bp = None

__all__ = ["router", "bp"]
