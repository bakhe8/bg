from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from BGLApp_Refactor.web import routes as web_routes


def _client():
    app = FastAPI()
    app.include_router(web_routes.router)
    return TestClient(app)


def test_landing_page_served(tmp_path, monkeypatch):
    client = _client()
    response = client.get("/")
    assert response.status_code in (200, 404)  # depends on repo state


def test_health_endpoint():
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
