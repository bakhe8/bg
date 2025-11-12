from __future__ import annotations

import io
import json
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from BGLApp_Refactor.api.routes import convert_excel as convert_route


def _build_client(monkeypatch, tmp_path):
    app = FastAPI()
    app.include_router(convert_route.router)

    convert_route.ARCHIVE_DIR = tmp_path
    convert_route.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    fake_gateway = mock.Mock()
    fake_gateway.convert_excel.return_value = json.dumps({"file_info": {}, "records": []})
    convert_route.gateway = fake_gateway

    monkeypatch.setattr(convert_route, "record_unknown_columns", mock.Mock())
    monkeypatch.setattr(convert_route, "log_event", mock.Mock())

    return TestClient(app), fake_gateway


def test_convert_endpoint_success(monkeypatch, tmp_path):
    client, gateway = _build_client(monkeypatch, tmp_path)
    file_content = io.BytesIO(b"dummy excel content")

    response = client.post(
        "/api/convert",
        files={"file": ("test.xlsx", file_content, "application/vnd.ms-excel")},
        data={"sheet": "all"},
    )

    assert response.status_code == 200
    assert "data" in response.json()
    gateway.convert_excel.assert_called_once()


def test_convert_endpoint_failure(monkeypatch, tmp_path):
    client, gateway = _build_client(monkeypatch, tmp_path)
    gateway.convert_excel.side_effect = ValueError("boom")

    response = client.post(
        "/api/convert",
        files={"file": ("test.xlsx", io.BytesIO(b"data"), "application/vnd.ms-excel")},
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "boom"


def test_convert_batch_mixed_results(monkeypatch, tmp_path):
    client, gateway = _build_client(monkeypatch, tmp_path)

    def side_effect(*args, **kwargs):
        if gateway.convert_excel.call_count == 2:
            raise RuntimeError("bad file")
        return json.dumps({"file_info": {}, "records": []})

    gateway.convert_excel.side_effect = side_effect

    files = [
        ("files", ("one.xlsx", io.BytesIO(b"1"), "application/vnd.ms-excel")),
        ("files", ("two.xlsx", io.BytesIO(b"2"), "application/vnd.ms-excel")),
    ]
    response = client.post("/api/convert/batch", files=files)

    assert response.status_code == 207
    payload = response.json()
    assert len(payload["results"]) == 1
    assert len(payload["errors"]) == 1
