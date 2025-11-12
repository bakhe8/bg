"""
FastAPI router for saving letters (JSON payloads).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, status

from main.api.logging_utils import log_event, new_uuid_name, sanitize_filename
from main.config import EXPORTS_DIR

router = APIRouter(prefix="/api/letters", tags=["letters"])

TARGET_DIR = EXPORTS_DIR
TARGET_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", status_code=status.HTTP_201_CREATED)
def save_letter(payload: dict = Body(...)):
    original_name = str(payload.get("filename") or "letter.json")
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
        return {"status": "saved", "path": str(target), "filename": filename}
    except Exception as exc:  # noqa: BLE001
        log_event(
            "save_letter_error",
            {"filename": filename, "path": str(target), "error": str(exc)},
            log_file="letters.log",
        )
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc


__all__ = ["router"]
