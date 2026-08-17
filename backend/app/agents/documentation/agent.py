from app.schemas.blueprint import (
    APIOutput,
    ArchitectureOutput,
    DatabaseOutput,
    DocumentationOutput,
    ImplementationOutput,
    RequirementOutput,
)


def plan_implementation(
    requirements: RequirementOutput,
    architecture: ArchitectureOutput,
    database: DatabaseOutput,
    api: APIOutput,
) -> ImplementationOutput:
    return ImplementationOutput(
        project_structure=[
            "frontend/src/components for reusable workflow and artifact UI",
            "frontend/src/lib for API clients and shared helpers",
            "backend/app/api for route handlers",
            "backend/app/agents for specialized planning agents",
            "backend/app/services for orchestration, persistence, and AI provider logic",
            "backend/app/schemas for Pydantic contracts",
        ],
        phases=[
            "Implement requirement extraction with structured output.",
            "Add supervisor orchestration and artifact persistence.",
            "Implement architecture, database, and API agents.",
            "Generate implementation and documentation artifacts.",
            "Run validation checks across all generated outputs.",
            "Connect frontend workflow UI to backend project APIs.",
        ],
        dependencies=[
            "fastapi",
            "pydantic",
            "motor",
            "react",
            "typescript",
            "tailwindcss",
            "axios",
        ],
        suggested_order=[
            "Stabilize backend contracts.",
            "Wire deterministic agents for end-to-end workflow.",
            "Add Gemini-backed provider implementation.",
            "Persist projects and agent outputs.",
            "Expand frontend inspection views.",
        ],
    )


def write_documentation(
    idea: str,
    requirements: RequirementOutput,
    architecture: ArchitectureOutput,
    database: DatabaseOutput,
    api: APIOutput,
) -> DocumentationOutput:
    return DocumentationOutput(
        overview=f"This project blueprint describes an MVP for: {idea.strip()}",
        setup_instructions=[
            "Copy .env.example to .env and provide required secrets locally.",
            "Run docker compose up --build to start frontend, backend, and MongoDB.",
            "Open the frontend workspace and submit a project idea.",
        ],
        architecture_notes=[
            architecture.architecture_pattern,
            f"The backend contains {len(architecture.components)} major components.",
            "Agent outputs are passed as typed models to preserve traceability.",
        ],
        api_notes=[
            f"The API design currently defines {len(api.endpoints)} endpoints.",
            api.authentication,
        ],
        development_guidelines=[
            "Keep prompts separate from application logic.",
            "Prefer structured Pydantic outputs over free-form text.",
            f"Ensure every requirement maps to database and API support; {len(database.collections)} collections are planned.",
            f"Use tests for the {len(requirements.functional_requirements)} captured functional requirements.",
        ],
    )
