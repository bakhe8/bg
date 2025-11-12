"""
Shared constants and lookup helpers for the refactor workspace.

During the migration this module simply proxies the legacy JSON data so
that behaviour remains identical. Once the refactor stabilises the
payloads can be copied here without any functional changes.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from transition.backend.reference_loader import load_bank_reference, load_column_aliases

from .paths import LEGACY_PATHS
from ..pdf.models import BankModel


REFERENCE_DIR = LEGACY_PATHS.reference_dir


@lru_cache(maxsize=1)
def get_bank_reference() -> List[Dict[str, Any]]:
    """Return the canonical bank list used by the converter."""
    return load_bank_reference()


def get_bank_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a bank entry using a case-insensitive lookup."""
    normalized = _normalize(name)
    for entry in get_bank_reference():
        if _normalize(entry.get("arabic") or entry.get("name") or "") == normalized:
            return entry
        for alias in entry.get("aliases", []):
            if _normalize(alias) == normalized:
                return entry
    return None


@lru_cache(maxsize=1)
def get_column_aliases() -> Dict[str, List[str]]:
    """Return the canonical column aliases mapping."""
    return load_column_aliases()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_bank_model(name: str) -> BankModel | None:
    entry = get_bank_by_name(name)
    if not entry:
        return None
    return BankModel.from_mapping(entry)


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


__all__ = [
    "REFERENCE_DIR",
    "get_bank_reference",
    "get_bank_by_name",
    "get_column_aliases",
    "load_json",
    "build_bank_model",
]
