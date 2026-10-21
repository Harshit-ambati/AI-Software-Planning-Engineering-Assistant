import json
from datetime import datetime
from hashlib import sha256


def run_metrics(run, ratings):
    details = [e["detail"] for e in run["events"] if e["status"] == "completed"]
    report = run["artifacts"].get("validation", {})
    wall = (datetime.fromisoformat(run["updated_at"]) - datetime.fromisoformat(run["created_at"])).total_seconds()
    human = {
        key: round(sum(r["payload"][key] for r in ratings) / len(ratings), 2) if ratings else None
        for key in ("completeness", "correctness", "consistency")
    }
    return dict(
        scope_hash=sha256(
            json.dumps({"brief": run["brief"], "constraints": run["constraints_text"]}, sort_keys=True).encode()
        ).hexdigest()[:16],
        sources_hash=sha256(json.dumps(run["artifacts"].get("sources", []), sort_keys=True).encode()).hexdigest()[:16],
        requirements_hash=run.get("requirements_etag"),
        human_edited="requirements_original" in run["artifacts"],
        human_seeded="seed_provenance" in run["artifacts"],
        id=run["id"],
        version=run["version"],
        provider=run["provider"],
        model=run["model"],
        strategy=run.get("strategy", "staged"),
        use_memory=bool(run.get("use_memory", True)),
        status=run["status"],
        is_live=run["provider"] == "gemini",
        brief_hash=sha256(run["brief"].encode()).hexdigest()[:16],
        generation_ms=sum(d.get("duration_ms", 0) for d in details),
        wall_seconds=round(wall, 2),
        input_tokens=sum(d.get("input_tokens", 0) for d in details),
        output_tokens=sum(d.get("output_tokens", 0) for d in details),
        reasoning_tokens=sum(d.get("reasoning_tokens", 0) for d in details),
        model_attempts=sum(d.get("attempts", 0) for d in details) if run["provider"] == "gemini" else 0,
        linked_coverage=report.get("coverage_percent"),
        semantic_coverage=report.get("semantic_coverage_percent"),
        findings=len(report.get("findings", [])),
        human_scores=human,
        human_review_count=len(ratings),
        prompt_versions=sorted({d["prompt_version"] for d in details if "prompt_version" in d}),
        limitations=[
            "Demo latency and zero tokens do not measure model performance.",
            "Generation timing excludes embedding calls; wall time includes queueing and human review.",
            "Telemetry counts completed stages; failed-stage calls may be absent. Human ratings are subjective.",
        ],
    )


def evaluate_retrieval(memory, project_id, payload, provider):
    results = []
    for item in payload.queries:
        hits = memory.search(project_id, item.query, limit=payload.k, unique_documents=True)
        expected = set(item.expected_document_ids)
        found = [hit["document_id"] for hit in hits]
        relevant = len(expected.intersection(found))
        reciprocal = next((1 / rank for rank, doc_id in enumerate(found, 1) if doc_id in expected), 0)
        results.append(
            dict(
                query=item.query,
                expected_document_ids=sorted(expected),
                retrieved=hits,
                precision_at_k=round(relevant / payload.k, 4),
                recall_at_k=round(relevant / len(expected), 4),
                reciprocal_rank=round(reciprocal, 4),
            )
        )
    return dict(
        corpus_hash=sha256(
            json.dumps(
                sorted(
                    [
                        {key: doc[key] for key in ("id", "title", "content")}
                        for doc in memory.store.knowledge(project_id)
                    ],
                    key=lambda doc: doc["id"],
                ),
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        k=payload.k,
        query_count=len(results),
        embedding=provider.embedding_namespace,
        mode="semantic" if provider.settings.ai_provider == "gemini" else "lexical demo",
        precision_at_k=round(sum(r["precision_at_k"] for r in results) / len(results), 4),
        recall_at_k=round(sum(r["recall_at_k"] for r in results) / len(results), 4),
        mrr=round(sum(r["reciprocal_rank"] for r in results) / len(results), 4),
        queries=results,
        definition="Document-level ranking with deduplicated source IDs. Precision uses k even if fewer hits are returned. Labels are user-supplied relevance judgments.",
    )
