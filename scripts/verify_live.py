"""Opt-in live Gemini integration check using synthetic data in an isolated store.

Run: .venv/Scripts/python.exe scripts/verify_live.py [--include-baseline]
Makes billable provider requests. Never prints or saves the API key.
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.store import now  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

BRIEF = "Design a university library system: students search books, reserve available copies, borrow books, return books and view loan due dates. Librarians manage books and approve borrowing."


def require(response):
    if response.status_code >= 400:
        raise RuntimeError(
            f"API request failed ({response.status_code}): {response.json().get('detail', 'Unavailable')}"
        )
    return response.json()


def wait(client, run_id, expected, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = require(client.get(f"/api/runs/{run_id}"))
        if value["status"] in expected:
            return value
        if value["status"] == "failed":
            raise RuntimeError(value["error"])
        time.sleep(0.5)
    raise RuntimeError("Live verification timed out. Provider requests may still have consumed quota.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-baseline", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    settings = Settings()
    if not settings.gemini_api_key or settings.gemini_api_key in ("your-key-here", "replace-me"):
        print("Set GEMINI_API_KEY in the root .env before live verification. No requests were made.")
        return 2
    target = ROOT / "docs" / "evaluation" / "live-verification.json"
    result = dict(
        checked_at=now(),
        model=settings.gemini_model,
        embedding_model=settings.gemini_embedding_model,
        mode="live",
        status="failed",
        scenario="synthetic university library",
        includes_baseline=args.include_baseline,
    )
    (ROOT / "data").mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="live-verification-", dir=ROOT / "data") as directory:
            settings = settings.model_copy(
                update=dict(data_dir=Path(directory), qdrant_url="", ai_provider="gemini", app_access_token="")
            )
            with TestClient(create_app(settings)) as client:
                project = require(
                    client.post("/api/projects", json={"name": "Synthetic live verification", "brief": BRIEF})
                )
                pid = project["id"]
                document = require(
                    client.post(
                        f"/api/projects/{pid}/knowledge",
                        json={
                            "title": "Library reservation policy",
                            "content": "Library reservations expire after 48 hours. Students may have at most three active loans. Return operations must preserve the loan audit trail.",
                        },
                    )
                )
                retrieval = require(
                    client.post(
                        f"/api/projects/{pid}/evaluation/retrieval",
                        json={
                            "k": 1,
                            "queries": [
                                {
                                    "query": "How long can a library reservation remain active?",
                                    "expected_document_ids": [document["id"]],
                                }
                            ],
                        },
                    )
                )
                result["retrieval"] = retrieval["result"]
                value = require(
                    client.post(
                        f"/api/projects/{pid}/runs",
                        json={
                            "brief": BRIEF,
                            "constraints": "Use a modular monolith for a small student team.",
                            "review_required": True,
                        },
                    )
                )
                rid = value["id"]
                wait(client, rid, {"awaiting_review"}, args.timeout)
                require(client.post(f"/api/runs/{rid}/approve"))
                completed = wait(client, rid, {"passed", "needs_attention"}, args.timeout)
                for format in ("json", "markdown", "openapi"):
                    response = client.get(f"/api/runs/{rid}/export/{format}")
                    if response.status_code != 200:
                        raise RuntimeError(f"{format} export failed after live generation ({response.status_code}).")
                if args.include_baseline:
                    baseline = require(
                        client.post(
                            f"/api/projects/{pid}/runs",
                            json={
                                "brief": BRIEF,
                                "constraints": "Use a modular monolith for a small student team.",
                                "strategy": "single_prompt",
                                "review_required": False,
                                "use_memory": True,
                            },
                        )
                    )
                    wait(client, baseline["id"], {"passed", "needs_attention"}, args.timeout)
                result["runs"] = require(client.get(f"/api/projects/{pid}/evaluations"))["runs"]
                result["validation"] = completed["artifacts"]["validation"]
                result["status"] = (
                    "workflow_verified" if retrieval["result"]["recall_at_k"] == 1 else "retrieval_expectation_failed"
                )
                result["limitations"] = [
                    "One synthetic live scenario is not a broad quality evaluation.",
                    "A completed workflow may still contain validation findings. Human correctness ratings were not invented.",
                ]
    except RuntimeError as exc:
        result["error"] = str(exc).replace(settings.gemini_api_key, "[redacted]")[:500]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: verification failed; inspect configuration and connectivity."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Live verification: {result['status']}. Report: {target}")
    return 0 if result["status"] == "workflow_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
