from app.schemas.blueprint import ArchitectureOutput, RequirementOutput


def design_architecture(requirements: RequirementOutput) -> ArchitectureOutput:
    return ArchitectureOutput(
        components=[
            "React TypeScript frontend for the engineering workspace",
            "FastAPI backend for workflow orchestration and typed APIs",
            "MongoDB persistence for projects, sessions, agent outputs, and validation reports",
            "Provider-agnostic AI service for Gemini first and future LLM providers",
            "Supervisor workflow service to pass structured context between agents",
        ],
        technologies=[
            "React",
            "TypeScript",
            "Tailwind CSS",
            "FastAPI",
            "Pydantic",
            "MongoDB",
            "Docker Compose",
        ],
        architecture_pattern="Modular monolith with supervisor-led agent orchestration",
        communication=[
            "Frontend calls backend REST endpoints through Axios.",
            "Backend agents exchange Pydantic models instead of raw conversation history.",
            "Persistence layer stores each generated artifact with project traceability.",
        ],
        decisions=[
            "Use FastAPI because the API contracts map cleanly to Pydantic models.",
            "Use MongoDB because blueprint artifacts are nested documents that evolve by stage.",
            "Keep AI providers behind a service boundary so Gemini can be replaced or extended later.",
            f"Design covers {len(requirements.functional_requirements)} functional requirements from intake.",
        ],
    )
