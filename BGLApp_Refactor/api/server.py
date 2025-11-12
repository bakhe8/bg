"""
FastAPI entrypoint for the refactor workspace.

يعرض الراوترات الجديدة بينما يظل التطبيق الأصلي متاحًا عبر WSGI mount
حتى تكتمل عملية النقل بالكامل.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles

from main.api.server import app as legacy_app

from ..core.config.paths import REFACTOR_ASSETS_DIR, REFACTOR_WEB_DIR
from .routes import aliases, convert_excel, health, review, save_letter
from ..web import routes as web_routes

app = FastAPI(title="BGLApp Refactor API", version="2.0.0")

for router in (
    convert_excel.router,
    aliases.router,
    save_letter.router,
    review.router,
    health.router,
    web_routes.router,
):
    app.include_router(router)

app.mount("/assets", StaticFiles(directory=REFACTOR_ASSETS_DIR), name="assets")
app.mount("/web", StaticFiles(directory=REFACTOR_WEB_DIR), name="web")
app.mount("/legacy", WSGIMiddleware(legacy_app))

__all__ = ["app"]
