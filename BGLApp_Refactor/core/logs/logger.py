"""
JSON logger utilities for BGLApp.

These functions replicate the behaviour from ``main.api.logging_utils`` so
new code imports them from the refactor tree. Legacy modules can delegate
back here to avoid divergence.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable
from uuid import uuid4

from BGLApp_Refactor.core.config.paths import LEGACY_PATHS

LOGS_DIR = LEGACY_PATHS.logs_dir
_LOG_FORMAT = os.environ.get("BGLAPP_LOG_FORMAT", "json").lower()


def log_event(event: str, metadata: Dict[str, Any], log_file: str = "api.log") -> None:
    """
    Append a JSON entry to the specified log file and mirror to ``app.log``.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "metadata": metadata,
    }
    _append_entry(entry, log_file)
    if log_file != "app.log":
        _append_entry(entry, "app.log")


def sanitize_filename(name: str | None, fallback: str = "file") -> str:
    """Remove reserved path characters to keep filenames safe for Windows."""
    if not name:
        return fallback
    cleaned = "".join(char for char in name if char not in '\\/:*?"<>|').strip()
    return cleaned or fallback


def count_records(payload: Any) -> int:
    """
    Count the records present in the converter output regardless of shape.
    """
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list):
            return len(records)
        sheets = payload.get("sheets")
        if isinstance(sheets, dict):
            total = 0
            for sheet_payload in sheets.values():
                rows = sheet_payload.get("records") if isinstance(sheet_payload, dict) else []
                if isinstance(rows, list):
                    total += len(rows)
            return total
    return 0


def new_uuid_name(prefix: str, extension: str = "") -> str:
    """Create a unique filename with a UUID4 suffix."""
    suffix = extension if extension.startswith(".") or not extension else f".{extension}"
    return f"{prefix}_{uuid4().hex}{suffix}"


def _append_entry(entry: Dict[str, Any], log_file: str) -> None:
    path = LOGS_DIR / log_file
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        if _LOG_FORMAT == "text":
            handle.write(f"{entry['timestamp']} | {entry['event']} | {entry['metadata']}\n")
        else:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")


def set_log_format(fmt: str) -> None:
    global _LOG_FORMAT
    _LOG_FORMAT = fmt.lower()


@dataclass(slots=True)
class LoggerManager:
    """
    Small convenience wrapper for modules that want dependency injection.
    """

    component: str

    def log(self, event: str, payload: Dict[str, Any] | None = None, *, log_file: str = "api.log") -> None:
        log_event(event or self.component, payload or {}, log_file=log_file)

    def sanitize_filename(self, name: str | None, default: str = "file") -> str:
        return sanitize_filename(name, default)

    def count_records(self, dataset: Any) -> int:
        return count_records(dataset)

    def new_uuid_name(self, prefix: str, suffix: str = "") -> str:
        return new_uuid_name(prefix, suffix)


__all__ = [
    "LOGS_DIR",
    "LoggerManager",
    "log_event",
    "sanitize_filename",
    "count_records",
    "new_uuid_name",
    "set_log_format",
]
