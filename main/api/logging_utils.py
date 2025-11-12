from __future__ import annotations

from typing import Any, Dict

from BGLApp_Refactor.core.logs.logger import (
    log_event as _log_event,
    sanitize_filename as _sanitize_filename,
    count_records as _count_records,
    new_uuid_name as _new_uuid_name,
)


def log_event(event: str, metadata: Dict[str, Any], log_file: str = "api.log") -> None:
    """Compatibility shim that forwards to the refactor logger implementation."""
    _log_event(event, metadata, log_file)


def sanitize_filename(name: str | None, fallback: str = "file") -> str:
    return _sanitize_filename(name, fallback)


def count_records(payload: Any) -> int:
    return _count_records(payload)


def new_uuid_name(prefix: str, extension: str = "") -> str:
    return _new_uuid_name(prefix, extension)
