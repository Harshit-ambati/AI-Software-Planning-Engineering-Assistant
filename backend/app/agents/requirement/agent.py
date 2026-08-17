from app.schemas.blueprint import RequirementOutput


def analyze_requirements(idea: str) -> RequirementOutput:
    normalized = idea.strip().rstrip(".")
    lower_idea = normalized.lower()

    actors = ["End user", "Administrator"]
    if any(term in lower_idea for term in ["delivery", "order", "marketplace", "booking"]):
        actors.extend(["Service provider", "Operations team"])
    if any(term in lower_idea for term in ["payment", "subscription", "checkout"]):
        actors.append("Payment processor")

    functional_requirements = [
        f"Users can create and manage records for: {normalized}.",
        "Users can authenticate and maintain a profile.",
        "Administrators can review, update, and moderate platform data.",
        "The system stores project activity and important state changes.",
        "Users can search, filter, and inspect relevant information.",
    ]

    if "track" in lower_idea or "delivery" in lower_idea or "order" in lower_idea:
        functional_requirements.append("Users can track the current status of orders or requests.")
    if "payment" in lower_idea or "checkout" in lower_idea or "delivery" in lower_idea:
        functional_requirements.append("Users can complete secure payment-related workflows.")

    return RequirementOutput(
        actors=sorted(set(actors)),
        functional_requirements=functional_requirements,
        non_functional_requirements=[
            "The system should provide predictable API responses with typed schemas.",
            "The system should protect sensitive data and never expose secrets to clients.",
            "The system should support observability through structured logs.",
            "The system should be maintainable through clear frontend/backend separation.",
        ],
        assumptions=[
            "The MVP will use web clients before native mobile applications.",
            "External integrations will be abstracted behind services.",
            "Role-based access can start with user and administrator roles.",
        ],
        constraints=[
            "The MVP should avoid autonomous repository modification.",
            "The MVP should prioritize blueprint quality before advanced integrations.",
        ],
    )
