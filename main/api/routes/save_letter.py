"""Deprecated Flask blueprint kept for backwards compatibility.

The save-letter endpoint now lives in ``BGLApp_Refactor.api.routes.save_letter``.
"""

from BGLApp_Refactor.api.routes.save_letter import router  # type: ignore

bp = None

__all__ = ["router", "bp"]
