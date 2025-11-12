from __future__ import annotations

from __future__ import annotations

from pathlib import Path


def register_view_routes(app, web_root: Path) -> None:  # noqa: D401
    """
    Legacy shim retained for backwards compatibility.

    The Flask UI has been migrated to FastAPI; this function now does nothing.
    """

    app.logger.warning("register_view_routes is deprecated; use FastAPI router instead.")
