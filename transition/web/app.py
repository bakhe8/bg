from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from transition.web.routes import register_all_routes

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT_DIR / "main" / "bg_ui"
ARCHIVE_DIR = ROOT_DIR / "main" / "data" / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(WEB_DIR),
    static_url_path="",
)
app.config["SECRET_KEY"] = os.environ.get("EXCEL_JSON_SECRET", "excel-json-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB per upload

register_all_routes(app, WEB_DIR, ARCHIVE_DIR)


def run():
    """Helper to run the Flask dev server."""
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    run()
