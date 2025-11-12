"""Helpers to register Flask blueprints for the transition web layer."""

from __future__ import annotations

from pathlib import Path
from flask import Flask

from .api_routes import register_api_routes
from .view_routes import register_view_routes


def register_all_routes(app: Flask, web_root: Path, archive_dir: Path) -> None:
    """Register both API and view blueprints on the given Flask app."""
    register_view_routes(app, web_root)
    register_api_routes(app, archive_dir)
