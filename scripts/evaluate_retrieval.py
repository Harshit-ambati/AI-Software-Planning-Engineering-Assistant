"""Reproducible lexical retrieval baseline. No model calls or API key required."""

import json
import sys
import tempfile
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.evaluation import evaluate_retrieval  # noqa: E402
from app.memory import Memory  # noqa: E402
from app.models import CreateProject, RetrievalEvaluation  # noqa: E402
from app.provider import Provider  # noqa: E402
from app.store import Store  # noqa: E402


def main():
    scenarios = json.loads((ROOT / "docs/evaluation/scenarios.json").read_text(encoding="utf-8"))
    query_texts = {
        "delivery": "cancellation before preparation delivery status audit",
        "library": "reservations expire student active loans",
        "inventory": "transfers adjustments stock ledger negative inventory",
        "appointments": "slot booked twice late cancellation reason",
        "campus": "restricted equipment administrator approval conflicting reservations",
    }
    (ROOT / "data").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="retrieval-baseline-", dir=ROOT / "data") as directory:
        settings = Settings(
            data_dir=Path(directory), ai_provider="demo", gemini_api_key="", qdrant_url="", _env_file=None
        )
        provider, store = Provider(settings), Store(settings.data_dir)
        project = store.create_project(
            CreateProject(
                name="Retrieval baseline",
                brief="Compare synthetic project policies using labeled document-level retrieval.",
            )
        )
        memory = Memory(settings, provider, store)
        try:
            queries = []
            for scenario in scenarios:
                doc_id = str(uuid5(NAMESPACE_URL, "forma-benchmark-policy-" + scenario["id"]))
                title = scenario["id"] + " policy"
                memory.ingest(project["id"], doc_id, title, scenario["policy"])
                store.add_knowledge(project["id"], title, scenario["policy"], doc_id)
                queries.append(dict(query=query_texts[scenario["id"]], expected_document_ids=[doc_id]))
            result = evaluate_retrieval(memory, project["id"], RetrievalEvaluation(k=3, queries=queries), provider)
            result["limitations"] = [
                "Five synthetic policies and lexically similar queries only; no claim of semantic search quality.",
                "Human labels were defined before ranking. Repeat with paraphrased held-out queries and live embeddings for a semantic comparison.",
            ]
            target = ROOT / "docs/evaluation/offline-retrieval.json"
            target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(
                f"Lexical baseline: P@3={result['precision_at_k']}, Recall@3={result['recall_at_k']}, MRR={result['mrr']}"
            )
            print(f"Report: {target}")
        finally:
            memory.close()


if __name__ == "__main__":
    main()
