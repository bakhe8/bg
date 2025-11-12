from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict

from main.config import LOGS_DIR


def log_event(event: str, metadata: Dict[str, Any], log_file: str = "api.log") -> None:
    """Append a JSON log entry with a UTC timestamp."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "metadata": metadata,
    }
    _append_entry(entry, log_file)
    if log_file != "app.log":
        _append_entry(entry, "app.log")


def sanitize_filename(name: str | None, fallback: str = "file") -> str:
    """Remove problematic characters from filenames to avoid traversal issues."""
    if not name:
        return fallback
    cleaned = "".join(char for char in name if char not in '\\/:*?"<>|').strip()
    return cleaned or fallback


def count_records(payload: Any) -> int:
    """Count records in the converter payload (single or multi-sheet)."""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        if isinstance(payload.get("records"), list):
            return len(payload["records"])
        sheets = payload.get("sheets")
        if isinstance(sheets, dict):
            total = 0
            for sheet in sheets.values():
                rows = sheet.get("records") if isinstance(sheet, dict) else []
                if isinstance(rows, list):
                    total += len(rows)
            return total
    return 0


def new_uuid_name(prefix: str, extension: str = "") -> str:
    """Generate a deterministic filename using UUID4."""
    suffix = extension if extension.startswith(".") or not extension else f".{extension}"
    return f"{prefix}_{uuid4().hex}{suffix}"


def _append_entry(entry: Dict[str, Any], log_file: str) -> None:
    path = LOGS_DIR / log_file
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False))
        handle.write("\n")
