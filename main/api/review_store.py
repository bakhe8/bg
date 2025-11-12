from __future__ import annotations

from typing import Dict, List

from BGLApp_Refactor.core.review import store as refactor_store


def record_unknown_columns(filename: str, columns: List[Dict]) -> None:
    refactor_store.record_unknown_columns(filename, columns)


def load_unknown_columns() -> List[Dict]:
    return refactor_store.load_unknown_columns()


def ignore_column(label: str) -> None:
    refactor_store.ignore_column(label)


def unignore_column(label: str) -> None:
    refactor_store.unignore_column(label)


def list_ignored_columns() -> List[str]:
    return refactor_store.list_ignored_columns()
