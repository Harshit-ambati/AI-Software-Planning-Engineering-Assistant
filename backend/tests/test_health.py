from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_application_status():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_name" in body
    assert "database_connected" in body

