"""
FastAPI router for alias management.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from main.api.logging_utils import log_event
from main.config import COLUMN_ALIASES_PATH
from transition.backend.reference_loader import load_column_aliases

router = APIRouter(prefix="/api/aliases", tags=["aliases"])


class AliasRequest(BaseModel):
    canonical: str
    alias: str


@router.get("", status_code=status.HTTP_200_OK)
def list_aliases():
    aliases = load_column_aliases()
    return {"aliases": aliases}


@router.post("", status_code=status.HTTP_201_CREATED)
def add_alias(payload: AliasRequest):
    canonical = payload.canonical.strip()
    alias = payload.alias.strip()

    if not canonical or not alias:
        raise HTTPException(
            status_code=400,
            detail={"error": "الرجاء اختيار الحقل القياسي وإدخال اسم العمود."},
        )

    aliases = load_column_aliases()
    if canonical not in aliases:
        raise HTTPException(status_code=400, detail={"error": "الحقل القياسي المحدد غير معروف."})

    alias_key = alias.lower().strip()
    existing = {value.lower().strip() for value in aliases.get(canonical, [])}
    if alias_key in existing:
        return {"status": "exists", "message": "العمود مضاف مسبقًا."}

    raw_data = _load_raw_config()
    raw_aliases = raw_data.setdefault(canonical, [])
    raw_aliases.append(alias)
    _write_raw_config(raw_data)
    load_column_aliases.cache_clear()
    log_event(
        "add_alias",
        {"canonical": canonical, "alias": alias},
        log_file="aliases.log",
    )
    return {"status": "added", "canonical": canonical, "alias": alias}


def _load_raw_config():
    if not COLUMN_ALIASES_PATH.exists():
        raise FileNotFoundError(f"لم يتم العثور على ملف الأعمدة المرجعي: {COLUMN_ALIASES_PATH}")
    with COLUMN_ALIASES_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_raw_config(data):
    with COLUMN_ALIASES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


__all__ = ["router"]
