from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from transition.backend.excel_to_json_converter import ExcelToJsonConverter

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "main" / "bg_ui"
ARCHIVE_DIR = BASE_DIR / "main" / "data" / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(WEB_DIR),
    static_url_path="",
)
app.config["SECRET_KEY"] = os.environ.get("EXCEL_JSON_SECRET", "excel-json-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB per upload


@app.route("/")
def serve_index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/api/convert", methods=["POST"])
def api_convert_excel():
    uploaded_file = request.files.get("file")
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "لم يتم تحديد ملف Excel"}), 400

    sheet_value = _parse_sheet_value(request.form.get("sheet", "all"))
    clean_mode = (request.form.get("clean", "true").lower() != "false")
    optimize_mode = (request.form.get("optimize", "true").lower() != "false")

    suffix = Path(uploaded_file.filename).suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        uploaded_file.save(tmp.name)
        temp_path = tmp.name

    try:
        app.logger.info("API convert: sheet=%s clean=%s optimize=%s", sheet_value, clean_mode, optimize_mode)
        converter = ExcelToJsonConverter(
            clean_data=clean_mode,
            optimize_memory=optimize_mode,
        )
        json_output = converter.convert_excel_to_json(
            temp_path,
            sheet_name=sheet_value,
            output_file=None,
        )

        data = json.loads(json_output)
        archive_payload(uploaded_file.filename, data)
        return jsonify({"data": data})
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.route("/health", methods=["GET"])
def healthcheck():
    return {"status": "ok"}, 200


def archive_payload(filename: str, payload: dict):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archive_name = ARCHIVE_DIR / f"conversion_{timestamp}_{sanitize_name(filename)}.json"
    archive_name.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sanitize_name(value: str) -> str:
    return "".join(char for char in value if char not in '\\/:*?"<>|').strip() or "file"


def _parse_sheet_value(raw_value: str | None):
    if not raw_value:
        return 0
    cleaned = raw_value.strip()
    if not cleaned:
        return 0
    if cleaned.lower() == "all":
        return "all"
    try:
        return int(cleaned)
    except ValueError:
        return cleaned


def run():
    """Helper to run the Flask dev server."""
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    run()
