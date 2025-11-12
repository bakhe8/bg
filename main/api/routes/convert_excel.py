"""Deprecated Flask blueprint for legacy imports.

The actual implementation now lives in ``BGLApp_Refactor.api.routes.convert_excel``.
This module simply exposes the FastAPI router for compatibility with old imports.
"""

from BGLApp_Refactor.api.routes.convert_excel import router  # type: ignore

bp = None  # Flask blueprint removed

__all__ = ["router", "bp"]
