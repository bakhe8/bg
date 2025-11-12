"""
FastAPI router for review utilities.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from BGLApp_Refactor.core.review import (
    ignore_column,
    list_ignored_columns,
    load_unknown_columns,
    unignore_column,
)
from main.api.logging_utils import log_event

router = APIRouter(prefix="/api/review", tags=["review"])


class ColumnLabel(BaseModel):
    label: str


@router.get("/unknown-columns", status_code=status.HTTP_200_OK)
def review_unknown_columns():
    columns = load_unknown_columns()
    return {"columns": columns, "ignored": list_ignored_columns()}


@router.post("/ignore", status_code=status.HTTP_200_OK)
def review_ignore_column(payload: ColumnLabel):
    label = payload.label.strip()
    if not label:
        raise HTTPException(status_code=400, detail={"error": "الرجاء تحديد اسم العمود"})
    ignore_column(label)
    log_event("review_ignore", {"label": label}, log_file="review.log")
    return {"status": "ignored", "label": label}


@router.delete("/ignore", status_code=status.HTTP_200_OK)
def review_unignore_column(payload: ColumnLabel):
    label = payload.label.strip()
    if not label:
        raise HTTPException(status_code=400, detail={"error": "الرجاء تحديد اسم العمود"})
    unignore_column(label)
    log_event("review_unignore", {"label": label}, log_file="review.log")
    return {"status": "restored", "label": label}


__all__ = ["router"]
