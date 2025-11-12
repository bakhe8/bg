from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from BGLApp_Refactor.core.config.paths import (
    REFACTOR_TEMPLATES_DIR,
    REFACTOR_WEB_DIR,
)

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(REFACTOR_TEMPLATES_DIR))


def _file_response(filename: str) -> FileResponse:
    path = REFACTOR_WEB_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    return FileResponse(path)


@router.get("/", include_in_schema=False)
def landing_page():
    return _file_response("index.html")


@router.get("/review", include_in_schema=False)
def review_page():
    return _file_response("review.html")


@router.get("/monitor", include_in_schema=False)
def monitor_page():
    return _file_response("monitor.html")


@router.get("/preview", include_in_schema=False)
def preview_template(request: Request):
    template = "letter_template.html"
    if not (REFACTOR_TEMPLATES_DIR / template).exists():
        raise HTTPException(status_code=404, detail="Template not available")
    return templates.TemplateResponse(template, {"request": request})


@router.get("/reports", include_in_schema=False)
def reports_placeholder():
    # Placeholder until bespoke reports UI is migrated
    return {"status": "coming_soon"}


@router.get("/health", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}


__all__ = ["router"]
