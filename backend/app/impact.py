"""Conservative, explainable change propagation over declared artifact links."""


def analyze_impact(artifacts, proposed):
    baseline = artifacts.get("requirements", {})
    old = {r["id"]: r for r in baseline.get("functional", [])}
    new = {r["id"]: r for r in proposed.get("functional", [])}
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    modified = sorted(key for key in old.keys() & new.keys() if old[key] != new[key])
    cross_cutting = [
        key
        for key in ("summary", "actors", "non_functional", "assumptions", "questions", "out_of_scope")
        if baseline.get(key) != proposed.get(key)
    ]
    changed = set(added + removed + modified)
    affected = {stage: {} for stage in ("architecture", "database", "apis", "implementation")}
    keys = dict(architecture="components", database="entities", apis="endpoints", implementation="tasks")
    for stage, key in keys.items():
        for record in artifacts.get(stage, {}).get(key, []):
            refs = sorted(changed.intersection(record.get("requirement_ids", [])))
            if refs or cross_cutting:
                affected[stage][record["id"]] = dict(
                    id=record["id"],
                    label=record.get("name", record.get("title", record.get("summary", record["id"]))),
                    reasons=(["Requirement changed: " + ", ".join(refs)] if refs else [])
                    + (["Cross-cutting scope or quality requirements changed"] if cross_cutting else []),
                    direct=True,
                )
    for endpoint in artifacts.get("apis", {}).get("endpoints", []):
        linked = sorted(set(endpoint["entity_ids"]).intersection(affected["database"]))
        if linked:
            item = affected["apis"].setdefault(
                endpoint["id"], dict(id=endpoint["id"], label=endpoint["summary"], reasons=[], direct=False)
            )
            item["reasons"].append("Uses affected entities: " + ", ".join(linked))
    tasks = artifacts.get("implementation", {}).get("tasks", [])
    while True:
        added_task = False
        for task in tasks:
            deps = sorted(set(task["depends_on"]).intersection(affected["implementation"]))
            if deps and task["id"] not in affected["implementation"]:
                affected["implementation"][task["id"]] = dict(
                    id=task["id"],
                    label=task["title"],
                    reasons=["Depends on affected tasks: " + ", ".join(deps)],
                    direct=False,
                )
                added_task = True
        if not added_task:
            break
    any_change = bool(changed or cross_cutting)
    return dict(
        added=added,
        removed=removed,
        modified=modified,
        cross_cutting=cross_cutting,
        affected={stage: list(rows.values()) for stage, rows in affected.items()},
        regenerate=["documentation", "validation"] if any_change else [],
        unlinked_new_requirements=added,
        limitations=[
            "Impact follows declared links and task dependencies, not source-code analysis.",
            "New requirements may need new components and entities not present in the baseline.",
            "A changed scope or NFR conservatively flags every existing design record.",
        ],
    )
