"""Load reference data (column aliases, bank mappings) for the converter."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Any

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _load_json(name: str) -> Any:
    path = CONFIG_DIR / name
    with path.open(encoding='utf-8-sig') as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_column_aliases() -> Dict[str, List[str]]:
    data = _load_json('column_aliases.json')
    normalized = {}
    for canonical, aliases in data.items():
        alias_set = {canonical.lower().strip()}
        alias_set.update(alias.lower().strip() for alias in aliases)
        normalized[canonical] = sorted(alias_set)
    return normalized


@lru_cache(maxsize=1)
def load_bank_reference() -> List[Dict[str, Any]]:
    payload = _load_json('banks.json')
    for entry in payload:
        entry['aliases'] = [alias.lower().strip() for alias in entry.get('aliases', [])]
    return payload


@lru_cache(maxsize=1)
def load_normalization_rules() -> Dict[str, List[str]]:
    return _load_json('normalization_rules.json')
