from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from BGLApp_Refactor.api.routes import save_letter as letter_route


def _client(monkeypatch, tmp_path):
    app = FastAPI()
    app.include_router(letter_route.router)
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(letter_route, "TARGET_DIR", tmp_path, raising=False)
    monkeypatch.setattr(letter_route, "log_event", lambda *args, **kwargs: None)
    return TestClient(app)


def test_save_letter_writes_file(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    payload = {
        "filename": "original.json",
        "bank_name": "Bank",
        "data": {"value": 1},
    }
    response = client.post("/api/letters", json=payload)
    assert response.status_code == 201
    data = response.json()
    saved_path = tmp_path / data["filename"]
    assert saved_path.exists()
    assert '"bank_name": "Bank"' in saved_path.read_text(encoding="utf-8")
