from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from transition.backend import ExcelToJsonConverter


def register_api_routes(app, archive_dir: Path) -> None:
    blueprint = Blueprint("api_routes", __name__)

    def archive_payload(filename: str, payload: dict) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = archive_dir / f"conversion_{timestamp}_{_sanitize_name(filename)}.json"
        archive_name.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @blueprint.route("/api/convert", methods=["POST"])
    def convert_excel():
        uploaded_file = request.files.get("file")
        if not uploaded_file or uploaded_file.filename == "":
            return jsonify({"error": "لم يتم تحديد ملف Excel"}), 400

        sheet_value = _parse_sheet_value(request.form.get("sheet", "all"))
        clean_mode = (request.form.get("clean", "true").lower() != "false")
        optimize_mode = (request.form.get("optimize", "true").lower() != "false")

        suffix = Path(uploaded_file.filename).suffix or ".xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            uploaded_file.save(tmp_file.name)
            temp_path = tmp_file.name

        try:
            app.logger.info(
                "API convert request: sheet=%s clean=%s optimize=%s",
                sheet_value,
                clean_mode,
                optimize_mode,
            )
            converter = ExcelToJsonConverter(clean_data=clean_mode, optimize_memory=optimize_mode)
            json_output = converter.convert_excel_to_json(temp_path, sheet_name=sheet_value, output_file=None)
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

    app.register_blueprint(blueprint)


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


def _sanitize_name(value: str) -> str:
    return "".join(char for char in value if char not in '\\/:*?\"<>|').strip() or "file"
