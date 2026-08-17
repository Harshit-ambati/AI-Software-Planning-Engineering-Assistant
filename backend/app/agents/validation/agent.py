from app.schemas.blueprint import (
    APIOutput,
    ArchitectureOutput,
    DatabaseOutput,
    RequirementOutput,
    ValidationIssue,
    ValidationOutput,
    WorkflowStage,
)


def validate_blueprint(
    requirements: RequirementOutput,
    architecture: ArchitectureOutput,
    database: DatabaseOutput,
    api: APIOutput,
) -> ValidationOutput:
    issues: list[ValidationIssue] = []
    warnings: list[str] = []

    if not requirements.functional_requirements:
        issues.append(
            ValidationIssue(
                stage=WorkflowStage.REQUIREMENTS,
                severity="error",
                message="No functional requirements were captured.",
            )
        )

    if not architecture.components:
        issues.append(
            ValidationIssue(
                stage=WorkflowStage.ARCHITECTURE,
                severity="error",
                message="Architecture does not define system components.",
            )
        )

    if not database.collections:
        issues.append(
            ValidationIssue(
                stage=WorkflowStage.DATABASE,
                severity="error",
                message="Database design does not define collections.",
            )
        )

    if not api.endpoints:
        issues.append(
            ValidationIssue(
                stage=WorkflowStage.API,
                severity="error",
                message="API design does not define endpoints.",
            )
        )

    tracking_required = any("track" in item.lower() for item in requirements.functional_requirements)
    tracking_supported = any("status" in endpoint.path or "track" in endpoint.description.lower() for endpoint in api.endpoints)
    if tracking_required and not tracking_supported:
        issues.append(
            ValidationIssue(
                stage=WorkflowStage.API,
                severity="error",
                message="Tracking requirement is not covered by an API status or tracking endpoint.",
            )
        )

    if len(api.endpoints) < 4:
        warnings.append("API surface may be too small for the captured requirements.")

    error_count = sum(1 for issue in issues if issue.severity == "error")

    return ValidationOutput(
        status="FAIL" if error_count else "PASS",
        issues=issues,
        warnings=warnings,
        recommendations=[
            "Add LLM-backed generation behind the existing structured agent contracts.",
            "Persist each artifact as an immutable version for auditability.",
            "Add human approval checkpoints before future code-generation features.",
        ],
    )
