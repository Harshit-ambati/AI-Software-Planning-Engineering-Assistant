import time

import pytest
from app.config import Settings
from app.demo import fixture
from app.main import create_app
from app.models import SCHEMAS
from app.validation import validate
from fastapi.testclient import TestClient

BRIEF = "Build a food delivery application with ordering, tracking and cancellation."


@pytest.fixture
def settings(tmp_path):
    return Settings(
        data_dir=tmp_path, ai_provider="demo", gemini_api_key="", app_access_token="", qdrant_url="", _env_file=None
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def project(client, name="Delivery workspace"):
    response = client.post("/api/projects", json={"name": name, "brief": BRIEF})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def wait(client, run_id, statuses):
    for _ in range(150):
        response = client.get(f"/api/runs/{run_id}")
        assert response.status_code == 200
        value = response.json()
        if value["status"] in statuses:
            return value
        if value["status"] == "failed":
            pytest.fail(value["error"])
        time.sleep(0.03)
    pytest.fail("Workflow did not settle")


def start(client, project_id, review=True):
    response = client.post(f"/api/projects/{project_id}/runs", json={"brief": BRIEF, "review_required": review})
    assert response.status_code == 202, response.text
    return response.json()["id"]


def test_review_persists_across_restart_and_exports(settings):
    app = create_app(settings)
    with TestClient(app) as client:
        pid = project(client)
        rid = start(client, pid)
        value = wait(client, rid, ["awaiting_review"])
        assert "requirements" in value["artifacts"]
        assert "architecture" not in value["artifacts"]
        assert client.post(f"/api/projects/{pid}/runs", json={"brief": BRIEF}).status_code == 409
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/runs/{rid}").json()["status"] == "awaiting_review"
        assert client.post(f"/api/runs/{rid}/approve").status_code == 202
        value = wait(client, rid, ["passed", "needs_attention"])
        assert value["status"] == "passed"
        assert value["artifacts"]["validation"]["coverage_percent"] == 100
        assert client.post(f"/api/runs/{rid}/approve").status_code == 409
        for stage, schema in SCHEMAS.items():
            schema.model_validate(value["artifacts"][stage])
        spec = client.get(f"/api/runs/{rid}/export/openapi").json()
        endpoint = spec["paths"]["/orders/{order_id}/tracking"]["get"]
        assert endpoint["parameters"][0]["required"] is True
        assert "schema" in endpoint["responses"]["200"]["content"]["application/json"]
        assert "x-requirement-ids" in endpoint
        assert "# Delivery workspace" in client.get(f"/api/runs/{rid}/export/markdown").text
        second = start(client, pid, review=False)
        wait(client, second, ["passed"])
        diff = client.get(f"/api/runs/{second}/compare/{rid}").json()
        assert diff["before_version"] == 1 and diff["after_version"] == 2
        assert diff["changes"] == []
        assert client.get(f"/api/runs/{rid}").json()["version"] == 1


def test_failure_resume_reuses_completed_stages(client, monkeypatch):
    pid = project(client)
    provider = client.app.state.provider
    original = provider.generate
    failed = False

    def unstable(stage, context):
        nonlocal failed
        if stage == "database" and not failed:
            failed = True
            raise RuntimeError("Simulated transient failure")
        return original(stage, context)

    monkeypatch.setattr(provider, "generate", unstable)
    rid = start(client, pid, review=False)
    for _ in range(150):
        value = client.get(f"/api/runs/{rid}").json()
        if value["status"] == "failed":
            break
        time.sleep(0.03)
    assert value["status"] == "failed"
    assert "architecture" in value["artifacts"]
    assert client.post(f"/api/runs/{rid}/resume").status_code == 202
    value = wait(client, rid, ["passed"])
    assert sum(e["stage"] == "requirements" and e["status"] == "completed" for e in value["events"]) == 1


def test_project_scoped_retrieval_and_source_provenance(client):
    first, second = project(client), project(client, "Private project")
    doc = {
        "title": "Delivery policy",
        "content": "Order tracking must retain a courier status history. Cancellation is allowed before preparation.",
    }
    response = client.post(f"/api/projects/{first}/knowledge", json=doc)
    assert response.status_code == 201, response.text
    assert client.post(f"/api/projects/{second}/knowledge/search", json={"query": "courier tracking"}).json() == []
    hits = client.post(f"/api/projects/{first}/knowledge/search", json={"query": "courier tracking"}).json()
    assert hits and hits[0]["document_id"] == response.json()["id"]
    rid = start(client, first)
    value = wait(client, rid, ["awaiting_review"])
    assert value["artifacts"]["sources"][0]["citation"] == hits[0]["citation"]
    assert client.post(f"/api/projects/{first}/knowledge/reindex").json()["indexed"] == 1


def test_validator_detects_corrupt_blueprint():
    artifacts = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    artifacts["apis"]["endpoints"] = artifacts["apis"]["endpoints"][:-1]
    artifacts["apis"]["endpoints"][0]["entity_ids"] = ["E-MISSING"]
    artifacts["database"]["relationships"][0]["target"] = "E-MISSING"
    artifacts["implementation"]["tasks"][0]["depends_on"] = ["T-6"]
    report = validate(artifacts)
    rules = {item["rule"] for item in report["findings"]}
    assert {"MISSING_COVERAGE", "UNKNOWN_ENTITY", "DEPENDENCY_CYCLE"} <= rules
    assert report["coverage_percent"] < 100


def test_duplicate_routes_normalize_parameter_names():
    artifacts = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    endpoint = artifacts["apis"]["endpoints"][2].copy()
    endpoint.update(id="API-extra", path="/orders/{different_name}/tracking")
    artifacts["apis"]["endpoints"].append(endpoint)
    assert "DUPLICATE_ROUTE" in {f["rule"] for f in validate(artifacts)["findings"]}


def test_auth_missing_input_and_invalid_transition(settings):
    settings.app_access_token = "test-only-secret"
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/projects").status_code == 401
        client.headers["Authorization"] = "Bearer test-only-secret"
        assert client.post("/api/projects", json={"name": "   ", "brief": BRIEF}).status_code == 422
        assert client.get("/api/projects/missing").status_code == 404
        assert client.post("/api/runs/missing/approve").status_code == 404
        assert client.get("/api/config").json()["provider"] == "demo"


def test_live_mode_without_key_never_returns_demo(settings):
    settings.ai_provider = "gemini"
    with TestClient(create_app(settings)) as client:
        pid = project(client)
        assert client.post(f"/api/projects/{pid}/runs", json={"brief": BRIEF}).status_code == 503


def test_rejected_review_remains_immutable_and_can_be_revised(client):
    pid = project(client)
    first = start(client, pid)
    before = wait(client, first, ["awaiting_review"])
    assert client.post(f"/api/runs/{first}/reject").json()["status"] == "rejected"
    assert client.post(f"/api/runs/{first}/approve").status_code == 409
    second = start(client, pid, review=False)
    wait(client, second, ["passed"])
    old = client.get(f"/api/runs/{first}").json()
    assert old["status"] == "rejected" and old["artifacts"] == before["artifacts"]
    other = project(client, "Different project")
    third = start(client, other, review=False)
    wait(client, third, ["passed"])
    assert client.get(f"/api/runs/{third}/compare/{second}").status_code == 400


def test_interrupted_work_is_not_silently_restarted(settings):
    from app.models import CreateProject, CreateRun
    from app.store import Store

    store = Store(settings.data_dir)
    pid = store.create_project(CreateProject(name="Interrupted example", brief=BRIEF))["id"]
    rid = store.create_run(pid, CreateRun(brief=BRIEF, review_required=False), "demo", "food-delivery-fixture-v2")["id"]
    store.status(rid, "running")
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/runs/{rid}").json()["status"] == "interrupted"
        assert client.post(f"/api/runs/{rid}/resume").status_code == 202
        wait(client, rid, ["passed"])


def test_invalid_api_paths_cannot_be_exported_as_openapi(client):
    pid = project(client)
    rid = start(client, pid, review=False)
    value = wait(client, rid, ["passed"])
    artifact = value["artifacts"]["apis"]
    artifact["endpoints"][0]["path"] = "/orders/{{broken}}"
    client.app.state.store.artifact(rid, "apis", artifact)
    assert client.get(f"/api/runs/{rid}/export/openapi").status_code == 409
    assert client.get(f"/api/runs/{rid}/export/json").status_code == 200
