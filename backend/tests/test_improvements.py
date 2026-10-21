from copy import deepcopy

from app.demo import fixture
from app.impact import analyze_impact
from app.models import SCHEMAS
from app.validation import validate
from test_workflow import BRIEF, project, start, wait


def test_requirement_edits_are_audited_and_used_downstream(client, monkeypatch):
    pid = project(client)
    rid = start(client, pid)
    before = wait(client, rid, ["awaiting_review"])
    edited = deepcopy(before["artifacts"]["requirements"])
    edited["functional"][0]["title"] = "Browse only restaurants that are open"
    captured = []
    original = client.app.state.provider.generate

    def capture(stage, context):
        if stage == "architecture":
            captured.append(context["upstream"]["requirements"])
        return original(stage, context)

    monkeypatch.setattr(client.app.state.provider, "generate", capture)
    response = client.post(
        f"/api/runs/{rid}/review/requirements",
        json={"expected_etag": before["requirements_etag"], "requirements": edited},
    )
    assert response.status_code == 200, response.text
    assert response.json()["requirements_etag"] != before["requirements_etag"]
    assert (
        client.post(
            f"/api/runs/{rid}/review/requirements",
            json={"expected_etag": before["requirements_etag"], "requirements": edited},
        ).status_code
        == 409
    )
    history = client.get(f"/api/runs/{rid}/review/history").json()
    assert len(history) == 1 and history[0]["before_content"] == before["artifacts"]["requirements"]
    assert history[0]["after_content"] == edited
    assert client.post(f"/api/runs/{rid}/approve").status_code == 202
    final = wait(client, rid, ["passed"])
    assert captured == [edited]
    assert final["artifacts"]["requirements"] == edited
    assert final["artifacts"]["requirements_original"] == before["artifacts"]["requirements"]
    assert (
        client.post(
            f"/api/runs/{rid}/review/requirements",
            json={"expected_etag": final["requirements_etag"], "requirements": edited},
        ).status_code
        == 409
    )


def test_invalid_requirement_edits_are_rejected(client):
    rid = start(client, project(client))
    value = wait(client, rid, ["awaiting_review"])
    requirements = value["artifacts"]["requirements"]
    requirements["functional"][0]["acceptance_criteria"] = ["   "]
    assert (
        client.post(
            f"/api/runs/{rid}/review/requirements",
            json={"expected_etag": value["requirements_etag"], "requirements": requirements},
        ).status_code
        == 422
    )
    requirements["functional"][0]["acceptance_criteria"] = ["Valid criterion"]
    requirements["functional"][0]["id"] = requirements["functional"][1]["id"]
    assert (
        client.post(
            f"/api/runs/{rid}/review/requirements",
            json={"expected_etag": value["requirements_etag"], "requirements": requirements},
        ).status_code
        == 422
    )


def test_impact_propagates_entities_and_task_dependencies():
    artifacts = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    proposed = deepcopy(artifacts["requirements"])
    proposed["functional"][0]["description"] += "; filter restaurants by delivery area"
    impact = analyze_impact(artifacts, proposed)
    assert impact["modified"] == ["FR-1"]
    assert next(t for t in impact["affected"]["implementation"] if t["id"] == "T-6")["direct"] is False
    assert next(a for a in impact["affected"]["apis"] if a["id"] == "API-4")["direct"] is False
    assert impact["regenerate"] == ["documentation", "validation"]
    proposed = deepcopy(artifacts["requirements"])
    assert not any(analyze_impact(artifacts, proposed)["affected"].values())
    proposed["non_functional"][0]["target"] = "p95 latency below 200ms"
    assert len(analyze_impact(artifacts, proposed)["affected"]["apis"]) == 6


def test_seeded_revision_preserves_baseline_and_rejects_cross_project_parent(client):
    pid = project(client)
    rid = start(client, pid, review=False)
    baseline = wait(client, rid, ["passed"])
    edited = deepcopy(baseline["artifacts"]["requirements"])
    edited["functional"][0]["priority"] = "should"
    payload = {"brief": BRIEF, "parent_run_id": rid, "requirements_seed": edited}
    response = client.post(f"/api/projects/{pid}/runs", json=payload)
    assert response.status_code == 202, response.text
    next_run = wait(client, response.json()["id"], ["awaiting_review"])
    assert next_run["artifacts"]["requirements"] == edited
    assert next_run["parent_run_id"] == rid
    assert client.get(f"/api/runs/{rid}").json()["artifacts"] == baseline["artifacts"]
    assert client.post(f"/api/projects/{project(client, 'Another workspace')}/runs", json=payload).status_code == 400
    assert (
        client.post(f"/api/projects/{pid}/runs", json={"brief": BRIEF, "requirements_seed": edited}).status_code == 422
    )


def test_single_prompt_baseline_and_measurements(client, monkeypatch):
    pid = project(client)
    calls = []
    original = client.app.state.provider.generate

    def capture(stage, context):
        calls.append(stage)
        return original(stage, context)

    monkeypatch.setattr(client.app.state.provider, "generate", capture)
    assert (
        client.post(f"/api/projects/{pid}/runs", json={"brief": BRIEF, "strategy": "single_prompt"}).status_code == 422
    )
    response = client.post(
        f"/api/projects/{pid}/runs",
        json={"brief": BRIEF, "strategy": "single_prompt", "review_required": False, "use_memory": False},
    )
    value = wait(client, response.json()["id"], ["passed"])
    assert calls == ["blueprint", "critique"]
    assert value["artifacts"]["sources"] == []
    metrics = client.get(f"/api/projects/{pid}/evaluations").json()["runs"][0]
    assert metrics["strategy"] == "single_prompt" and not metrics["is_live"]
    assert metrics["model_attempts"] == metrics["input_tokens"] == 0
    assert metrics["semantic_coverage"] is None
    rating = {
        "reviewer": "Test reviewer",
        "completeness": 4,
        "correctness": 3,
        "consistency": 5,
        "notes": "Synthetic human rubric test",
    }
    assert client.post(f"/api/runs/{value['id']}/evaluation/ratings", json=rating).status_code == 201
    assert client.get(f"/api/projects/{pid}/evaluations").json()["runs"][0]["human_scores"]["correctness"] == 3
    assert (
        client.post(f"/api/runs/{value['id']}/evaluation/ratings", json=rating | {"completeness": 6}).status_code == 422
    )


def test_retrieval_benchmark_uses_project_labels_and_unique_documents(client):
    pid = project(client)
    doc = client.post(
        f"/api/projects/{pid}/knowledge",
        json={"title": "Courier tracking", "content": "Courier tracking delivery status history. " * 100},
    ).json()
    payload = {"k": 2, "queries": [{"query": "courier tracking", "expected_document_ids": [doc["id"]]}]}
    response = client.post(f"/api/projects/{pid}/evaluation/retrieval", json=payload)
    assert response.status_code == 201, response.text
    result = response.json()["result"]
    assert result["precision_at_k"] == 0.5 and result["recall_at_k"] == result["mrr"] == 1
    assert len(result["queries"][0]["retrieved"]) == 1
    assert result["mode"] == "lexical demo"
    other = project(client, "Isolated knowledge workspace")
    assert client.post(f"/api/projects/{other}/evaluation/retrieval", json=payload).status_code == 422
    assert len(client.get(f"/api/projects/{pid}/evaluations").json()["retrieval"]) == 1


def test_semantic_review_requires_real_evidence_and_complete_assessments():
    artifacts = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    critique = {
        "findings": [],
        "limitations": [],
        "assessments": [
            {
                "requirement_id": "FR-3",
                "status": "missing",
                "endpoint_ids": [],
                "explanation": "Tracking response has no status history.",
            },
            {
                "requirement_id": "FR-1",
                "status": "satisfied",
                "endpoint_ids": ["API-fabricated"],
                "explanation": "Not valid evidence",
            },
        ],
        "source_assessments": [],
    }
    report = validate(artifacts, critique, expected_semantics=True)
    rules = {f["rule"] for f in report["findings"]}
    assert {"SEMANTIC_GAP", "INVALID_REVIEW_EVIDENCE", "SEMANTIC_REVIEW_INCOMPLETE"} <= rules
    assert report["semantic_coverage_percent"] == 0
    assert report["coverage_percent"] == 100


def test_source_conformance_review_rejects_invented_citations():
    artifacts = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    critique = {
        "findings": [],
        "limitations": [],
        "source_assessments": [
            {
                "citation": "policy:1",
                "status": "conflict",
                "requirement_ids": ["FR-6"],
                "endpoint_ids": ["API-6"],
                "explanation": "Cancellation rule conflicts with the source policy.",
            },
            {
                "citation": "invented:1",
                "status": "compliant",
                "requirement_ids": ["FR-1"],
                "endpoint_ids": [],
                "explanation": "Unknown source",
            },
        ],
    }
    report = validate(artifacts, critique, sources=[{"citation": "policy:1"}])
    assert {"SOURCE_CONFLICT", "INVALID_SOURCE_EVIDENCE"} <= {f["rule"] for f in report["findings"]}
    assert len(report["source_assessments"]) == 1


def test_concurrent_edit_cannot_overwrite_another_review(client):
    from concurrent.futures import ThreadPoolExecutor

    rid = start(client, project(client))
    before = wait(client, rid, ["awaiting_review"])
    payloads = []
    for title in ("Concurrent reviewer A", "Concurrent reviewer B"):
        reqs = deepcopy(before["artifacts"]["requirements"])
        reqs["functional"][0]["title"] = title
        payloads.append(dict(expected_etag=before["requirements_etag"], requirements=reqs))
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(
            executor.map(
                lambda payload: client.post(f"/api/runs/{rid}/review/requirements", json=payload).status_code, payloads
            )
        )
    assert sorted(statuses) == [200, 409]
    assert len(client.get(f"/api/runs/{rid}/review/history").json()) == 1


def test_existing_database_migrates_without_losing_runs(tmp_path):
    import sqlite3

    from app.store import Store

    path = tmp_path / "workspace.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript(
            "CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT, brief TEXT, constraints_text TEXT, created_at TEXT); CREATE TABLE runs (id TEXT PRIMARY KEY, project_id TEXT, version INTEGER, brief TEXT, constraints_text TEXT, review_required INTEGER, provider TEXT, model TEXT, status TEXT, created_at TEXT, updated_at TEXT, error TEXT);"
        )
        db.execute("INSERT INTO projects VALUES (?,?,?,?,?)", ("p", "Existing", BRIEF, "", "2026-10-21T00:00:00+00:00"))
        db.execute(
            "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "r",
                "p",
                1,
                BRIEF,
                "",
                1,
                "demo",
                "fixture",
                "passed",
                "2026-10-21T00:00:00+00:00",
                "2026-10-21T00:00:00+00:00",
                None,
            ),
        )
    store = Store(tmp_path)
    value = store.run("r")
    assert value["strategy"] == "staged" and value["use_memory"] == 1
    assert value["status"] == "passed"
    assert store.project("p")["name"] == "Existing"


def test_store_connections_are_closed_after_transaction(tmp_path):
    import sqlite3

    import pytest
    from app.store import Store

    store = Store(tmp_path)
    with store.db() as connection:
        connection.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")
