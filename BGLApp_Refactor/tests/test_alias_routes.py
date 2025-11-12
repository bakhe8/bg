from __future__ import annotations

import json
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from BGLApp_Refactor.api.routes import aliases as alias_route


def _client(monkeypatch, tmp_path):
    app = FastAPI()
    app.include_router(alias_route.router)
    path = tmp_path / "column_aliases.json"
    path.write_text(json.dumps({"amount": []}), encoding="utf-8")
    monkeypatch.setattr(alias_route, "COLUMN_ALIASES_PATH", path)

    def loader():
        return json.loads(path.read_text(encoding="utf-8"))

    loader.cache_clear = lambda: None  # type: ignore[attr-defined]
    monkeypatch.setattr(alias_route, "load_column_aliases", loader)
    monkeypatch.setattr(alias_route, "log_event", mock.Mock())
    return TestClient(app)


def test_list_aliases(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.get("/api/aliases")
    assert response.status_code == 200
    assert "aliases" in response.json()


def test_add_alias(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post("/api/aliases", json={"canonical": "amount", "alias": "قيمة"})
    assert response.status_code == 201
    assert response.json()["status"] == "added"
