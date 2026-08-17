from app.schemas.blueprint import DatabaseCollection, DatabaseOutput, RequirementOutput


def design_database(requirements: RequirementOutput) -> DatabaseOutput:
    collections = [
        DatabaseCollection(
            name="projects",
            description="Top-level software planning projects created by users.",
            fields=["_id", "title", "idea", "status", "created_at", "updated_at"],
        ),
        DatabaseCollection(
            name="project_sessions",
            description="Workflow execution sessions for a project.",
            fields=["_id", "project_id", "current_stage", "status", "started_at", "completed_at"],
        ),
        DatabaseCollection(
            name="agent_outputs",
            description="Structured output produced by each specialized agent.",
            fields=["_id", "project_id", "session_id", "stage", "payload", "model", "created_at"],
        ),
        DatabaseCollection(
            name="validation_reports",
            description="Coverage and consistency findings across generated artifacts.",
            fields=["_id", "project_id", "session_id", "status", "issues", "warnings", "created_at"],
        ),
    ]

    if any("payment" in item.lower() for item in requirements.functional_requirements):
        collections.append(
            DatabaseCollection(
                name="integration_events",
                description="External service callbacks and processing audit entries.",
                fields=["_id", "project_id", "provider", "event_type", "payload", "processed_at"],
            )
        )

    return DatabaseOutput(
        collections=collections,
        relationships=[
            "projects one-to-many project_sessions",
            "project_sessions one-to-many agent_outputs",
            "project_sessions one-to-one validation_reports",
        ],
        indexes=[
            "projects.status",
            "project_sessions.project_id",
            "agent_outputs.project_id + stage",
            "validation_reports.project_id + created_at",
        ],
    )
