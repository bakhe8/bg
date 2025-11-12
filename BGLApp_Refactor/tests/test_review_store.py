from __future__ import annotations

import json

from BGLApp_Refactor.core.review import store


def _setup_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "UNKNOWN_LOG", tmp_path / "unknown_columns.log")
    monkeypatch.setattr(store, "IGNORED_FILE", tmp_path / "ignored_columns.json")


def test_record_and_load_unknown_columns(tmp_path, monkeypatch):
    _setup_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "BGLApp_Refactor.core.review.store.load_column_aliases",
        lambda: {"iban": ["iban number"]},
    )

    store.record_unknown_columns(
        "sample.xlsx",
        [
            {"label": "New Column", "sheets": ["Sheet1"]},
            {"label": "IBAN Number", "sheets": ["Sheet2"]},
        ],
    )

    entries = store.load_unknown_columns()
    assert len(entries) == 1
    assert entries[0]["label"] == "New Column"
    assert entries[0]["files"] == ["sample.xlsx"]
    assert entries[0]["sheets"] == ["Sheet1"]


def test_ignore_and_unignore_columns(tmp_path, monkeypatch):
    _setup_paths(tmp_path, monkeypatch)

    store.ignore_column(" Temp Column ")
    assert store.list_ignored_columns() == ["temp column"]

    store.unignore_column("Temp Column")
    assert store.list_ignored_columns() == []
