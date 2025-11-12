from __future__ import annotations

from pathlib import Path
import json

from flask import Blueprint, request, jsonify

from main.api.logging_utils import log_event, sanitize_filename, new_uuid_name

bp = Blueprint("save_letter_route", __name__)
TARGET_DIR = Path("main/data/exports")
TARGET_DIR.mkdir(parents=True, exist_ok=True)


@bp.route("/api/letters", methods=["POST"])
def save_letter():
    payload = request.get_json(force=True) or {}
    original_name = payload.get("filename", "letter.json")
    ext = Path(original_name).suffix or ".json"
    filename = sanitize_filename(new_uuid_name("letter", ext), f"letter{ext}")
    target = TARGET_DIR / filename
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        target.write_text(body, encoding="utf-8")
        log_event(
            "save_letter",
            {
                "filename": filename,
                "original_name": original_name,
                "path": str(target),
                "size_bytes": len(body.encode("utf-8")),
                "bank_name": payload.get("bank_name"),
                "guarantee_number": payload.get("guarantee_number"),
                "contract_number": payload.get("contract_number"),
            },
            log_file="letters.log",
        )
        return jsonify({"status": "saved", "path": str(target), "filename": filename}), 201
    except Exception as exc:  # pylint: disable=broad-except
        log_event(
            "save_letter_error",
            {"filename": filename, "path": str(target), "error": str(exc)},
            log_file="letters.log",
        )
        return jsonify({"error": str(exc)}), 500
