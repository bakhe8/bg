from __future__ import annotations

import json
import secrets
import shutil
import tempfile
from pathlib import Path
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from main.api.alerts import notify_failure
from main.api.api_gateway import ApiGateway
from main.api.logging_utils import log_event, sanitize_filename, count_records, new_uuid_name
from main.api.models import (
    AliasAddRequest,
    BatchConvertEntry,
    BatchConvertResponse,
    ConvertResponse,
    IgnoreColumnRequest,
    LetterPayload,
)
from main.api.review_store import (
    ignore_column,
    list_ignored_columns,
    load_unknown_columns,
    record_unknown_columns,
    unignore_column,
)
from main.config import (
    ARCHIVES_DIR,
    ASSETS_DIR,
    COLUMN_ALIASES_PATH,
    EXPORTS_DIR,
    LOGS_DIR,
    REVIEW_DIR,
    TEMPLATES_DIR,
    WEB_DIR,
    settings,
)

READABLE_LOGS = {
    "convert": LOGS_DIR / "convert.log",
    "letters": LOGS_DIR / "letters.log",
    "review": LOGS_DIR / "review.log",
}
MONITOR_USER = settings.monitor_user
MONITOR_PASS = settings.monitor_pass
security = HTTPBasic(auto_error=False)

gateway = ApiGateway(ARCHIVES_DIR)

app = FastAPI(
    title="BGLApp API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/templates", StaticFiles(directory=TEMPLATES_DIR), name="templates")


@app.get("/")
async def serve_index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/preview")
async def serve_preview():
    return FileResponse(WEB_DIR / "templates" / "bg_view.html")


@app.get("/reports")
async def serve_reports():
    return FileResponse(WEB_DIR / "templates" / "report_view.html")


@app.get("/review")
async def serve_review(credentials: HTTPBasicCredentials = Depends(security)):
    require_monitor_auth(credentials)
    return FileResponse(WEB_DIR / "review.html")


@app.get("/monitor")
async def serve_monitor(credentials: HTTPBasicCredentials = Depends(security)):
    require_monitor_auth(credentials)
    return FileResponse(WEB_DIR / "monitor.html")


@app.post("/api/convert", response_model=ConvertResponse)
async def convert_excel(file: UploadFile = File(...), sheet: str = Form("all")):
    data = await _process_upload(file, sheet)
    return ConvertResponse(data=data)


@app.post("/api/convert/batch", response_model=BatchConvertResponse)
async def convert_excel_batch(
    files: List[UploadFile] = File(...),
    sheet: str = Form("all"),
):
    if not files:
        raise HTTPException(status_code=400, detail="لم يتم إرفاق أي ملف.")
    results: List[BatchConvertEntry] = []
    errors: List[dict] = []
    for upload in files:
        try:
            data = await _process_upload(upload, sheet)
            entry = BatchConvertEntry(
                filename=upload.filename or "upload.xlsx",
                records=count_records(data),
                data=data,
            )
            results.append(entry)
        except HTTPException as exc:
            errors.append({"filename": upload.filename, "error": exc.detail})
        except Exception as exc:  # pylint: disable=broad-except
            errors.append({"filename": upload.filename, "error": str(exc)})
            notify_failure("convert_batch_error", {"filename": upload.filename, "error": str(exc)})
    log_event(
        "convert_excel_batch",
        {
            "total": len(files),
            "success": len(results),
            "errors": len(errors),
            "sheet": sheet,
        },
        log_file="convert.log",
    )
    status_code = 200 if not errors else 207
    response = BatchConvertResponse(results=results, errors=errors)
    return JSONResponse(
        status_code=status_code,
        content=json.loads(response.model_dump_json()),
        media_type="application/json",
    )


@app.post("/api/letters")
async def save_letter(payload: LetterPayload):
    filename = sanitize_filename(payload.filename or new_uuid_name("letter", ".json"), "letter.json")
    target = EXPORTS_DIR / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload.data or payload.model_dump(), ensure_ascii=False, indent=2)
    try:
        target.write_text(body, encoding="utf-8")
    except OSError as exc:
        notify_failure("save_letter_error", {"filename": filename, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    log_event(
        "save_letter",
        {
            "filename": filename,
            "size_bytes": len(body.encode("utf-8")),
            "bank_name": payload.data.get("bank_name"),
            "guarantee_number": payload.data.get("guarantee_number"),
        },
        log_file="letters.log",
    )
    return {"status": "saved", "path": str(target), "filename": filename}


@app.get("/api/aliases")
async def list_aliases():
    aliases = load_column_aliases()
    return {"aliases": aliases}


@app.post("/api/aliases")
async def add_alias(request: AliasAddRequest):
    canonical = request.canonical.strip()
    alias = request.alias.strip()
    if not canonical or not alias:
        raise HTTPException(status_code=400, detail="الرجاء اختيار الحقل القياسي وإدخال اسم العمود.")
    aliases = load_column_aliases()
    if canonical not in aliases:
        raise HTTPException(status_code=400, detail="الحقل القياسي المحدد غير معروف.")
    normalized = alias.lower().strip()
    existing = {value.lower().strip() for value in aliases.get(canonical, [])}
    if normalized in existing:
        return {"status": "exists", "message": "العمود مضاف مسبقًا."}
    _persist_alias(canonical, alias)
    load_column_aliases.cache_clear()
    log_event(
        "add_alias",
        {"canonical": canonical, "alias": alias},
        log_file="aliases.log",
    )
    return {"status": "added", "canonical": canonical, "alias": alias}


@app.get("/api/review/unknown-columns")
async def review_unknown_columns():
    return {
        "columns": load_unknown_columns(),
        "ignored": list_ignored_columns(),
    }


@app.post("/api/review/ignore")
async def review_ignore_column(request: IgnoreColumnRequest):
    if not request.label.strip():
        raise HTTPException(status_code=400, detail="الرجاء تحديد اسم العمود.")
    ignore_column(request.label)
    log_event("review_ignore", {"label": request.label}, log_file="review.log")
    return {"status": "ignored", "label": request.label}


@app.delete("/api/review/ignore")
async def review_unignore_column(request: IgnoreColumnRequest):
    if not request.label.strip():
        raise HTTPException(status_code=400, detail="الرجاء تحديد اسم العمود.")
    unignore_column(request.label)
    log_event("review_unignore", {"label": request.label}, log_file="review.log")
    return {"status": "restored", "label": request.label}


@app.get("/api/logs")
async def read_logs(
    file: str,
    limit: int = 200,
    credentials: HTTPBasicCredentials = Depends(security),
):
    require_monitor_auth(credentials)
    path = READABLE_LOGS.get(file)
    if not path:
        raise HTTPException(status_code=400, detail="ملف السجل المطلوب غير مدعوم.")
    if not path.exists():
        return {"file": file, "entries": [], "message": "لا يوجد ملف سجل بعد."}
    lines = _tail_file(path, limit)
    return {"file": file, "entries": lines}


async def _process_upload(upload: UploadFile, sheet_value: str):
    if not upload:
        raise HTTPException(status_code=400, detail="لم يتم إرفاق ملف.")
    parsed_sheet = _parse_sheet_value(sheet_value)
    original_name = upload.filename or "upload.xlsx"
    ext = Path(original_name).suffix or ".xlsx"
    safe_name = sanitize_filename(new_uuid_name("upload", ext), ext)
    temp_path = ARCHIVE_DIR / safe_name
    try:
        with temp_path.open("wb") as dest:
            shutil.copyfileobj(upload.file, dest)
        json_output = gateway.convert_excel(str(temp_path), sheet=parsed_sheet)
        data = json.loads(json_output)
        unknown_columns = _extract_unknown_columns(data)
        if unknown_columns:
            record_unknown_columns(original_name, unknown_columns)
        log_event(
            "convert_excel",
            {
                "filename": original_name,
                "stored_name": safe_name,
                "sheet": parsed_sheet,
                "records": count_records(data),
                "size_bytes": temp_path.stat().st_size,
                "content_type": upload.content_type,
            },
            log_file="convert.log",
        )
        return data
    except Exception as exc:  # pylint: disable=broad-except
        log_event(
            "convert_excel_error",
            {"filename": original_name, "stored_name": safe_name, "sheet": parsed_sheet, "error": str(exc)},
            log_file="convert.log",
        )
        notify_failure("convert_excel_error", {"filename": original_name, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


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


def _extract_unknown_columns(payload: dict) -> list[dict]:
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
            unknown_cols = metadata.get("unknown_columns")
            if isinstance(unknown_cols, list):
                for col in unknown_cols:
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


def _persist_alias(canonical: str, alias: str) -> None:
    from json import load, dump

    config_path = COLUMN_ALIASES_PATH
    if not config_path.exists():
        raise HTTPException(status_code=500, detail="ملف الأعمدة المرجعي غير موجود.")
    with config_path.open(encoding="utf-8") as handle:
        data = load(handle)
    data.setdefault(canonical, []).append(alias)
    with config_path.open("w", encoding="utf-8") as handle:
        dump(data, handle, ensure_ascii=False, indent=2)


def _tail_file(path: Path, limit: int) -> list[str]:
    if limit <= 0:
        limit = 200
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    return [line.rstrip("\n") for line in lines[-limit:]]


def require_monitor_auth(credentials: HTTPBasicCredentials | None):
    if not MONITOR_USER or not MONITOR_PASS:
        return
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="يتطلب تسجيل دخول.",
            headers={"WWW-Authenticate": "Basic"},
        )
    correct_username = secrets.compare_digest(credentials.username, MONITOR_USER)
    correct_password = secrets.compare_digest(credentials.password, MONITOR_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="بيانات الاعتماد غير صحيحة.",
            headers={"WWW-Authenticate": "Basic"},
        )


if __name__ == "__main__":
    uvicorn.run("main.api.server:app", host="0.0.0.0", port=int(5000), reload=True)
