from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple


class ColumnMapper:
    """Resolve spreadsheet columns to canonical names using reference aliases."""

    def __init__(
        self,
        alias_map: Dict[str, List[str]],
        required_fields: List[str] | None = None,
        threshold: float = 0.9,
    ) -> None:
        self.alias_map = alias_map
        self.threshold = threshold
        self.required_fields = required_fields or list(alias_map.keys())
        self.lookup = self._build_lookup(alias_map)

    def _build_lookup(self, alias_map: Dict[str, List[str]]) -> Dict[str, str]:
        lookup = {}
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                lookup[self._normalize(alias)] = canonical
        return lookup

    def _normalize(self, label: str) -> str:
        return " ".join(label.strip().lower().split())

    def map_columns(self, columns: Iterable[str]) -> Tuple[Dict[str, str], List[str]]:
        rename_map: Dict[str, str] = {}
        unknown: List[str] = []
        for column in columns:
            key = self._normalize(column)
            canonical = self.lookup.get(key)
            if canonical:
                rename_map[column] = canonical
                continue

            candidate = self._match_fuzzy(key)
            if candidate:
                rename_map[column] = candidate
            else:
                unknown.append(column)
        return rename_map, unknown

    def _match_fuzzy(self, label: str) -> str | None:
        best_score = 0.0
        best_key = None
        for alias, canonical in self.lookup.items():
            score = SequenceMatcher(None, label, alias).ratio()
            if score > best_score:
                best_score = score
                best_key = canonical
        if best_score >= self.threshold:
            return best_key
        return None
