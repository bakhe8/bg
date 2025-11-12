from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from BGLApp_Refactor.api.routes import review as review_routes


def _create_client():
    app = FastAPI()
    app.include_router(review_routes.router)
    return TestClient(app)


def test_unknown_columns_endpoint(monkeypatch):
    monkeypatch.setattr(review_routes, "load_unknown_columns", lambda: [{"label": "New"}])
    monkeypatch.setattr(review_routes, "list_ignored_columns", lambda: ["old"])
    client = _create_client()

    response = client.get("/api/review/unknown-columns")
    assert response.status_code == 200
    payload = response.json()
    assert payload["columns"] == [{"label": "New"}]
    assert payload["ignored"] == ["old"]


def test_ignore_endpoint(monkeypatch):
    captured = {}
    monkeypatch.setattr(review_routes, "ignore_column", lambda label: captured.setdefault("label", label))
    monkeypatch.setattr(review_routes, "log_event", lambda *args, **kwargs: captured.setdefault("logged", True))
    client = _create_client()

    response = client.post("/api/review/ignore", json={"label": "Temp"})
    assert response.status_code == 200
    assert captured["label"] == "Temp"
    assert captured["logged"] is True


def test_ignore_endpoint_requires_label():
    client = _create_client()
    response = client.post("/api/review/ignore", json={"label": ""})
    assert response.status_code == 400


def test_unignore_endpoint(monkeypatch):
    captured = {}
    monkeypatch.setattr(review_routes, "unignore_column", lambda label: captured.setdefault("label", label))
    monkeypatch.setattr(review_routes, "log_event", lambda *args, **kwargs: captured.setdefault("logged", True))
    client = _create_client()

    response = client.request("DELETE", "/api/review/ignore", json={"label": "Temp"})
    assert response.status_code == 200
    assert captured["label"] == "Temp"
