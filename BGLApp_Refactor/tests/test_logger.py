from __future__ import annotations

import json

from BGLApp_Refactor.core.logs import logger


def test_log_event_writes_json_and_mirrors(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOGS_DIR", tmp_path)

    logger.log_event("convert_excel", {"filename": "sample.xlsx"}, log_file="convert.log")

    convert_path = tmp_path / "convert.log"
    app_path = tmp_path / "app.log"
    for target in (convert_path, app_path):
        assert target.exists()
        content = target.read_text(encoding="utf-8").strip()
        payload = json.loads(content)
        assert payload["event"] == "convert_excel"
        assert payload["metadata"]["filename"] == "sample.xlsx"


def test_sanitize_filename_removes_invalid_chars():
    dirty = 'bad:name<>|"'
    cleaned = logger.sanitize_filename(dirty)
    for char in '\\/:*?"<>|':
        assert char not in cleaned


def test_count_records_handles_sheet_payload():
    payload = {
        "sheets": {
            "A": {"records": [1, 2]},
            "B": {"records": [3]},
        }
    }
    assert logger.count_records(payload) == 3


def test_new_uuid_name_adds_extension():
    name = logger.new_uuid_name("upload", ".xlsx")
    assert name.startswith("upload_")
    assert name.endswith(".xlsx")
