"""
PDF generation utilities (wrapper around the legacy template rendering).

The refactor exposes a simple ``render_letter_html`` + ``generate_pdf``
API so new callers can avoid importing from ``main.api.server`` directly.
"""

from __future__ import annotations

import io
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

try:  # optional dependency during development
    from weasyprint import HTML
except Exception:  # pragma: no cover - handled gracefully
    HTML = None  # type: ignore

from ..config.paths import (
    LEGACY_PATHS,
    REFACTOR_ASSETS_DIR,
    REFACTOR_TEMPLATES_DIR,
    REFACTOR_WEB_DIR,
)
from ..config.constants import build_bank_model
from .models import BankModel, LetterModel

_env = Environment(
    loader=FileSystemLoader(str(REFACTOR_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)
_PDF_TEMPLATE = "letter_pdf.html"
_ASSETS_RELATIVE = (
    REFACTOR_ASSETS_DIR.relative_to(REFACTOR_WEB_DIR).as_posix()
    if REFACTOR_ASSETS_DIR.exists()
    else "assets"
)


def render_letter_html(payload: Dict[str, Any] | LetterModel) -> str:
    """
    Render the letter template using the refactor templates.

    Falls back to the legacy renderer if the new template is not found.
    """

    context = build_letter_context(payload)
    context.setdefault("assets_url", _ASSETS_RELATIVE)
    try:
        template = _env.get_template(_PDF_TEMPLATE)
        return template.render(**context)
    except TemplateNotFound:
        from main.api.server import render_letter_html as legacy_render_letter_html  # lazy import

        # Keep legacy behaviour if template missing during transition
        context.setdefault("assets_url", LEGACY_PATHS.assets_dir.relative_to(LEGACY_PATHS.web_dir).as_posix())
        return legacy_render_letter_html(context)


def generate_pdf(payload: Dict[str, Any] | LetterModel, *, extra: Dict[str, Any] | None = None) -> bytes:
    """Generate a PDF bytes payload using WeasyPrint if available."""

    if HTML is None:
        raise RuntimeError("WeasyPrint is not available in this environment.")

    context = build_letter_context(payload, extra=extra)
    context.setdefault("assets_url", _ASSETS_RELATIVE)
    template = _env.get_template(_PDF_TEMPLATE)
    html = template.render(**context)
    buffer = io.BytesIO()
    HTML(string=html, base_url=str(REFACTOR_WEB_DIR)).write_pdf(buffer)
    return buffer.getvalue()


def build_letter_context(payload: Dict[str, Any] | LetterModel, *, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Normalize letter payloads into the template context."""

    if isinstance(payload, LetterModel):
        context = payload.to_dict()
    else:
        context = dict(payload)

    if extra:
        context.update(extra)

    bank_name = context.get("bank_name")
    bank_model = build_bank_model(bank_name) if bank_name else None
    if bank_model:
        context.setdefault("bank", bank_model.to_dict())
        context.setdefault("bank_email", context.get("bank_email") or bank_model.email)
        context.setdefault("bank_center", context.get("bank_center") or bank_model.address)

    return context


__all__ = ["render_letter_html", "generate_pdf", "build_letter_context", "LetterModel", "BankModel"]
