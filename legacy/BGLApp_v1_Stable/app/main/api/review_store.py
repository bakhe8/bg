from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from main.config import COLUMN_ALIASES_PATH, REVIEW_DIR
from transition.backend.reference_loader import load_column_aliases

UNKNOWN_LOG = REVIEW_DIR / "unknown_columns.log"
IGNORED_FILE = REVIEW_DIR / "ignored_columns.json"


def record_unknown_columns(filename: str, columns: List[Dict[str, Any]]) -> None:
    if not columns:
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "columns": columns,
    }
    with UNKNOWN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False))
        handle.write("\n")


def load_unknown_columns() -> List[Dict[str, Any]]:
    entries = _read_unknown_log()
    alias_map = load_column_aliases()
    known_aliases = {_normalize(value) for aliases in alias_map.values() for value in aliases}
    ignored = set(_load_ignored())
    aggregated: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        filename = entry.get("filename")
        timestamp = entry.get("timestamp")
        for column in entry.get("columns", []):
            label = column.get("label")
            if not label:
                continue
            normalized = _normalize(label)
            if normalized in known_aliases or normalized in ignored:
                continue
            target = aggregated.setdefault(
                normalized,
                {
                    "label": label,
                    "count": 0,
                    "files": set(),
                    "sheets": set(),
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                },
            )
            target["count"] += 1
            if filename:
                target["files"].add(filename)
            for sheet in column.get("sheets", []) or []:
                target["sheets"].add(sheet)
            if timestamp and (not target["first_seen"] or timestamp < target["first_seen"]):
                target["first_seen"] = timestamp
            if timestamp and (not target["last_seen"] or timestamp > target["last_seen"]):
                target["last_seen"] = timestamp
    result = []
    for value in aggregated.values():
        value["files"] = sorted(value["files"])
        value["sheets"] = sorted(value["sheets"])
        result.append(value)
    return sorted(result, key=lambda item: item["last_seen"] or "", reverse=True)


def ignore_column(label: str) -> None:
    normalized = _normalize(label)
    if not normalized:
        return
    ignored = set(_load_ignored())
    ignored.add(normalized)
    _write_ignored(sorted(ignored))


def unignore_column(label: str) -> None:
    normalized = _normalize(label)
    if not normalized:
        return
    ignored = set(_load_ignored())
    if normalized in ignored:
        ignored.remove(normalized)
        _write_ignored(sorted(ignored))


def list_ignored_columns() -> List[str]:
    return _load_ignored()


def _read_unknown_log() -> List[Dict[str, Any]]:
    if not UNKNOWN_LOG.exists():
        return []
    entries = []
    with UNKNOWN_LOG.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _load_ignored() -> List[str]:
    if not IGNORED_FILE.exists():
        return []
    try:
        with IGNORED_FILE.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []


def _write_ignored(values: Iterable[str]) -> None:
    with IGNORED_FILE.open("w", encoding="utf-8") as handle:
        json.dump(list(values), handle, ensure_ascii=False, indent=2)


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
