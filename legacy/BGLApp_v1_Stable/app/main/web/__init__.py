"""
View route registration for the production web layer.
"""

from __future__ import annotations

from pathlib import Path
from flask import Flask

from .view_routes import register_view_routes as _register_view_routes


def register_view_routes(app: Flask, web_root: Path) -> None:
    _register_view_routes(app, web_root)
