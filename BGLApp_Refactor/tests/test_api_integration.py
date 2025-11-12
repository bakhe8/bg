from __future__ import annotations

from fastapi.testclient import TestClient

from BGLApp_Refactor.api.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_convert_without_file_returns_422():
    response = client.post("/api/convert")
    assert response.status_code == 422
