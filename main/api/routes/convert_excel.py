from __future__ import annotations

from pathlib import Path
import json
import time

from flask import Blueprint, request, jsonify

from main.api.api_gateway import ApiGateway
from main.api.logging_utils import log_event, sanitize_filename, count_records, new_uuid_name
from main.api.review_store import record_unknown_columns

bp = Blueprint("convert_excel_route", __name__)
ARCHIVE_DIR = Path("main/data/archives")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
gateway = ApiGateway(ARCHIVE_DIR)


@bp.route("/api/convert", methods=["POST"])
def convert_endpoint():
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "no file supplied"}), 400

    sheet_value = _parse_sheet_value(request.form.get("sheet"))
    payload, error = _handle_upload(uploaded, sheet_value)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"data": payload})


@bp.route("/api/convert/batch", methods=["POST"])
def convert_batch_endpoint():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "no files supplied"}), 400
    sheet_value = _parse_sheet_value(request.form.get("sheet"))
    results = []
    errors = []
    for uploaded in files:
        payload, error = _handle_upload(uploaded, sheet_value)
        if error:
            errors.append({"filename": uploaded.filename, "error": error})
        else:
            results.append(
                {
                    "filename": uploaded.filename,
                    "records": count_records(payload),
                    "data": payload,
                }
            )
    log_event(
        "convert_excel_batch",
        {
            "total": len(files),
            "success": len(results),
            "errors": len(errors),
            "sheet": sheet_value,
        },
        log_file="convert.log",
    )
    status_code = 200 if not errors else 207
    return jsonify({"results": results, "errors": errors}), status_code


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


def _handle_upload(uploaded, sheet_value):
    original_name = uploaded.filename or "upload.xlsx"
    ext = Path(original_name).suffix or ".xlsx"
    uuid_name = new_uuid_name("upload", ext)
    safe_name = sanitize_filename(uuid_name, uuid_name)
    temp_path = ARCHIVE_DIR / safe_name
    uploaded.save(temp_path)
    file_size = temp_path.stat().st_size if temp_path.exists() else None
    started = time.perf_counter()
    try:
        json_output = gateway.convert_excel(str(temp_path), sheet=sheet_value)
        data = json.loads(json_output)
        unknown_columns = _extract_unknown_columns(data)
        if unknown_columns:
            record_unknown_columns(original_name, unknown_columns)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        log_event(
            "convert_excel",
            {
                "filename": original_name,
                "stored_name": safe_name,
                "sheet": sheet_value,
                "records": count_records(data),
                "size_bytes": file_size,
                "duration_ms": duration_ms,
                "content_type": uploaded.mimetype,
            },
            log_file="convert.log",
        )
        return data, None
    except Exception as exc:  # pylint: disable=broad-except
        log_event(
            "convert_excel_error",
            {
                "filename": original_name,
                "stored_name": safe_name,
                "sheet": sheet_value,
                "error": str(exc),
            },
            log_file="convert.log",
        )
        return None, str(exc)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _extract_unknown_columns(payload: dict) -> list[dict]:
    def normalize_list(value):
        return value if isinstance(value, list) else []

    columns = []
    file_info = payload.get("file_info") or {}
    info_unknown = file_info.get("unknown_columns")
    if isinstance(info_unknown, list):
        columns.extend({"label": col, "sheets": [file_info.get("sheet_name")]} for col in info_unknown)
    elif isinstance(info_unknown, dict):
        for sheet, sheet_columns in info_unknown.items():
            for col in sheet_columns or []:
                columns.append({"label": col, "sheets": [sheet]})

    sheets = payload.get("sheets")
    if isinstance(sheets, dict):
        for sheet_name, sheet_payload in sheets.items():
            metadata = sheet_payload.get("metadata") or {}
            for col in normalize_list(metadata.get("unknown_columns")):
                columns.append({"label": col, "sheets": [sheet_name]})

    normalized = {}
    for entry in columns:
        label = (entry.get("label") or "").strip()
        if not label:
            continue
        key = label.lower()
        target = normalized.setdefault(key, {"label": label, "sheets": set()})
        for sheet in entry.get("sheets") or []:
            target["sheets"].add(sheet)
    result = []
    for value in normalized.values():
        result.append({"label": value["label"], "sheets": sorted(value["sheets"])})
    return result
