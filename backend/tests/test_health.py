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


def test_generate_blueprint_returns_structured_artifacts():
    with TestClient(app) as client:
        response = client.post(
            "/api/projects/blueprint",
            json={"idea": "Build an online food delivery application with order tracking."},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["requirements"]["functional_requirements"]
    assert body["architecture"]["components"]
    assert body["database"]["collections"]
    assert body["api"]["endpoints"]
    assert body["implementation"]["phases"]
    assert body["documentation"]["overview"]
    assert body["validation"]["status"] == "PASS"
