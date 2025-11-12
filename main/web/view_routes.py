from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, send_from_directory


def register_view_routes(app, web_root: Path) -> None:
    blueprint = Blueprint("main_view_routes", __name__, template_folder=str(web_root / "templates"))

    @blueprint.route("/")
    def landing_page():
        return send_from_directory(web_root, "index.html")

    @blueprint.route("/preview")
    def preview_template():
        return render_template("bg_view.html", title="معاينة الخطاب")

    @blueprint.route("/reports")
    def report_view():
        return render_template("report_view.html")

    @blueprint.route("/health")
    def healthcheck():
        return {"status": "ok"}, 200

    @blueprint.route("/review")
    def review_page():
        return send_from_directory(web_root, "review.html")

    app.register_blueprint(blueprint)
