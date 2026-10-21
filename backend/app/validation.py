"""Deterministic reference and coverage checks, independent of the model."""

import re
from collections import Counter


def validate(artifacts, critique=None, sources=None, expected_semantics=False):
    findings = []

    def issue(rule, artifact, reference, message, severity="error"):
        findings.append(dict(rule=rule, artifact=artifact, reference=reference, message=message, severity=severity))

    def records(stage, key):
        return artifacts.get(stage, {}).get(key, [])

    groups = {
        "requirements": records("requirements", "functional"),
        "architecture": records("architecture", "components"),
        "database": records("database", "entities"),
        "apis": records("apis", "endpoints"),
        "implementation": records("implementation", "tasks"),
    }
    for stage, rows in groups.items():
        if not rows:
            issue("EMPTY_ARTIFACT", stage, "", "Artifact must contain at least one record.")
        for key, count in Counter(row["id"] for row in rows).items():
            if count > 1:
                issue("DUPLICATE_ID", stage, key, "IDs must be unique within each artifact.")
    reqs = {row["id"] for row in groups["requirements"]}
    entities = {row["id"] for row in groups["database"]}
    tasks = {row["id"] for row in groups["implementation"]}
    for stage in ("architecture", "database", "apis", "implementation"):
        for row in groups[stage]:
            if not row["requirement_ids"]:
                issue("UNTRACED_RECORD", stage, row["id"], "No requirement is linked.")
            for ref in row["requirement_ids"]:
                if ref not in reqs:
                    issue("UNKNOWN_REQUIREMENT", stage, row["id"], f"Unknown requirement {ref}.")
    coverage = []
    for req in groups["requirements"]:
        row = dict(requirement_id=req["id"], title=req["title"])
        for stage in ("architecture", "database", "apis", "implementation"):
            row[stage] = [item["id"] for item in groups[stage] if req["id"] in item["requirement_ids"]]
            if not row[stage] and stage != "database":
                issue("MISSING_COVERAGE", stage, req["id"], f"{req['title']} has no linked {stage} record.")
        coverage.append(row)
    for relation in records("database", "relationships"):
        for ref in (relation["source"], relation["target"]):
            if ref not in entities:
                issue("UNKNOWN_ENTITY", "database", ref, "Relationship refers to a missing entity.")
    for entity in groups["database"]:
        for name, count in Counter(f["name"] for f in entity["fields"]).items():
            if count > 1:
                issue("DUPLICATE_FIELD", "database", entity["id"], f"Duplicate field {name}.")
        if not entity["indexes"]:
            issue("MISSING_INDEX", "database", entity["id"], "No indexes are recommended.", "warning")
    operations = set()
    for endpoint in groups["apis"]:
        # Parameter names do not distinguish routes: /orders/{id} == /orders/{order_id}.
        path = endpoint["path"]
        operation = endpoint["method"] + " " + re.sub(r"\{[^}]+\}", "{}", path)
        if operation in operations:
            issue("DUPLICATE_ROUTE", "apis", endpoint["id"], f"Duplicate route {operation}.")
        operations.add(operation)
        if not re.fullmatch(
            r"/(?:[A-Za-z0-9_-]+|\{[A-Za-z_][A-Za-z0-9_]*\})(?:/(?:[A-Za-z0-9_-]+|\{[A-Za-z_][A-Za-z0-9_]*\}))*/?|/",
            path,
        ):
            issue("INVALID_PATH", "apis", endpoint["id"], "Path must be an absolute REST path without query strings.")
        if path.count("{") != path.count("}"):
            issue("INVALID_PATH", "apis", endpoint["id"], "Unbalanced path parameters.")
        for ref in endpoint["entity_ids"]:
            if ref not in entities:
                issue("UNKNOWN_ENTITY", "apis", endpoint["id"], f"Unknown entity {ref}.")
        if endpoint["method"] in ("GET", "DELETE") and endpoint["request_fields"]:
            issue(
                "REQUEST_BODY",
                "apis",
                endpoint["id"],
                "GET/DELETE request bodies have inconsistent client support.",
                "warning",
            )
        if not endpoint["authenticated"] and endpoint["method"] != "GET":
            issue(
                "PUBLIC_WRITE",
                "apis",
                endpoint["id"],
                "Review authorization for this public write endpoint.",
                "warning",
            )
        if not endpoint["errors"]:
            issue("MISSING_ERRORS", "apis", endpoint["id"], "No failure cases are documented.", "warning")
    dependencies = {task["id"]: task["depends_on"] for task in groups["implementation"]}
    for task, refs in dependencies.items():
        for ref in refs:
            if ref not in tasks:
                issue("UNKNOWN_TASK", "implementation", task, f"Unknown dependency {ref}.")
    visited, active = set(), set()

    def visit(task):
        if task in active:
            issue("DEPENDENCY_CYCLE", "implementation", task, "Implementation tasks contain a dependency cycle.")
            return
        if task in visited:
            return
        active.add(task)
        for dependency in dependencies.get(task, []):
            visit(dependency)
        active.remove(task)
        visited.add(task)

    for task in dependencies:
        visit(task)
    if critique:
        findings.extend(critique["findings"])
    assessments = (critique or {}).get("assessments", [])
    source_assessments = (critique or {}).get("source_assessments", [])
    endpoint_map = {endpoint["id"]: endpoint for endpoint in groups["apis"]}
    accepted, seen = [], set()
    for assessment in assessments:
        ref = assessment["requirement_id"]
        ids = assessment["endpoint_ids"]
        valid = ref in reqs and ref not in seen and all(key in endpoint_map for key in ids)
        if assessment["status"] == "satisfied":
            valid = (
                valid
                and bool(ids)
                and any(ref in endpoint_map[key]["requirement_ids"] for key in ids if key in endpoint_map)
            )
        seen.add(ref)
        if not valid:
            issue(
                "INVALID_REVIEW_EVIDENCE",
                "validation",
                ref,
                "Semantic review contains duplicate/unknown references or unsupported satisfaction claims.",
            )
            continue
        accepted.append(assessment)
        if assessment["status"] != "satisfied":
            issue(
                "SEMANTIC_GAP",
                "apis",
                ref,
                assessment["explanation"],
                "error" if assessment["status"] == "missing" else "warning",
            )
    if expected_semantics:
        missing = reqs - {a["requirement_id"] for a in accepted}
        if missing:
            issue(
                "SEMANTIC_REVIEW_INCOMPLETE",
                "validation",
                ", ".join(sorted(missing)),
                "Not every requirement has a valid behavior assessment.",
                "warning",
            )
    citations = {source["citation"] for source in (sources or [])}
    accepted_sources, seen_sources = [], set()
    for assessment in source_assessments:
        citation = assessment["citation"]
        valid = (
            citation in citations
            and citation not in seen_sources
            and set(assessment["requirement_ids"]) <= reqs
            and set(assessment["endpoint_ids"]) <= endpoint_map.keys()
        )
        if assessment["status"] in ("compliant", "conflict"):
            valid = valid and bool(assessment["requirement_ids"] or assessment["endpoint_ids"])
        seen_sources.add(citation)
        if not valid:
            issue(
                "INVALID_SOURCE_EVIDENCE",
                "validation",
                citation,
                "Source review cites missing evidence or unknown blueprint references.",
            )
            continue
        accepted_sources.append(assessment)
        if assessment["status"] in ("conflict", "uncertain"):
            issue(
                "SOURCE_CONFLICT" if assessment["status"] == "conflict" else "SOURCE_UNCERTAIN",
                "validation",
                citation,
                assessment["explanation"],
                "error" if assessment["status"] == "conflict" else "warning",
            )
    if expected_semantics and citations - {s["citation"] for s in accepted_sources}:
        issue(
            "SOURCE_REVIEW_INCOMPLETE",
            "validation",
            "",
            "Some retrieved source passages have no valid conformance review.",
            "warning",
        )
    covered = sum(bool(row["architecture"] and row["apis"] and row["implementation"]) for row in coverage)
    return dict(
        semantic_assessments=accepted,
        semantic_coverage_percent=round(100 * sum(a["status"] == "satisfied" for a in accepted) / len(reqs))
        if accepted and reqs
        else None,
        source_assessments=accepted_sources,
        status="needs_attention" if findings else "passed",
        findings=findings,
        coverage=coverage,
        coverage_percent=round(100 * covered / len(reqs)) if reqs else 0,
        rule_version="2.0.0",
        checked_requirements=len(reqs),
        limitations=[
            "Coverage measures explicit links, not semantic correctness.",
            "Generated schemas, performance targets and security controls require implementation testing.",
        ]
        + (critique["limitations"] if critique else ["No LLM critique available."]),
    )
