"""Offline fault injection benchmark; not an evaluation of LLM design quality."""

import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.demo import fixture  # noqa: E402
from app.models import SCHEMAS  # noqa: E402
from app.validation import validate  # noqa: E402


def evaluate():
    baseline = {stage: fixture(stage) for stage in SCHEMAS if stage != "critique"}
    cases = []

    def case(name, expected, mutate):
        value = deepcopy(baseline)
        mutate(value)
        report = validate(value)
        rules = sorted({f["rule"] for f in report["findings"]})
        cases.append(dict(case=name, expected_rule=expected, detected=expected in rules, observed_rules=rules))

    case("Missing cancellation endpoint", "MISSING_COVERAGE", lambda a: a["apis"]["endpoints"].pop())
    case(
        "Unknown requirement reference",
        "UNKNOWN_REQUIREMENT",
        lambda a: a["apis"]["endpoints"][0]["requirement_ids"].append("FR-999"),
    )
    case("Dangling relationship", "UNKNOWN_ENTITY", lambda a: a["database"]["relationships"][0].update(target="E-999"))
    case(
        "Cyclic implementation plan",
        "DEPENDENCY_CYCLE",
        lambda a: a["implementation"]["tasks"][0]["depends_on"].append("T-6"),
    )
    case(
        "Duplicate operation",
        "DUPLICATE_ROUTE",
        lambda a: a["apis"]["endpoints"].append(deepcopy(a["apis"]["endpoints"][0])),
    )
    case("Unknown dependency", "UNKNOWN_TASK", lambda a: a["implementation"]["tasks"][0]["depends_on"].append("T-999"))
    case("Public write operation", "PUBLIC_WRITE", lambda a: a["apis"]["endpoints"][1].update(authenticated=False))
    case("Empty architecture", "EMPTY_ARTIFACT", lambda a: a["architecture"].update(components=[]))
    semantic = deepcopy(baseline)
    semantic["apis"]["endpoints"][2].update(
        path="/orders/{order_id}/receipt", summary="Download receipt; does not expose tracking status"
    )
    return dict(
        benchmark="Offline deterministic validator fault injection",
        fixture="food-delivery-fixture-v2",
        baseline_findings=validate(baseline)["findings"],
        cases=cases,
        expected_faults_detected=sum(c["detected"] for c in cases),
        injected_faults=len(cases),
        documented_blind_spot=dict(
            case="Linked endpoint has wrong business semantics",
            deterministic_findings=validate(semantic)["findings"],
            explanation="IDs still link correctly. Detecting this semantic mismatch requires model critique or human review.",
        ),
        limitations=[
            "One synthetic domain; no estimate of generalization or live model quality.",
            "Detection here is rule-trigger rate, not independently measured semantic precision/recall.",
        ],
    )


if __name__ == "__main__":
    result = evaluate()
    target = ROOT / "docs" / "evaluation" / "offline-validator.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Detected {result['expected_faults_detected']}/{result['injected_faults']} expected injected faults.")
    print(f"Report: {target}")
