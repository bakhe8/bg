from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from .paths import REFACTOR_ROOT

MANIFEST_PATH = REFACTOR_ROOT / "core" / "config" / "manifest.json"


@lru_cache(maxsize=1)
def load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def get_version() -> str:
    return str(load_manifest().get("version", "0.0.0-dev"))


def get_build_date() -> str:
    return str(load_manifest().get("build_date", "unknown"))


__all__ = ["load_manifest", "get_version", "get_build_date", "MANIFEST_PATH"]
