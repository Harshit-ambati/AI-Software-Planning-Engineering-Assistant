from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateProject(Contract):
    name: str = Field(min_length=3, max_length=100)
    brief: str = Field(min_length=30, max_length=12000)
    constraints: str = Field(default="", max_length=3000)


class CreateRun(Contract):
    brief: str = Field(min_length=30, max_length=12000)
    constraints: str = Field(default="", max_length=3000)
    review_required: bool = True
    strategy: Literal["staged", "single_prompt"] = "staged"
    use_memory: bool = True
    parent_run_id: str | None = None
    requirements_seed: "Requirements | None" = None


class Requirement(Contract):
    id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=3000)
    actor: str = Field(min_length=1, max_length=120)
    priority: Literal["must", "should", "could"]
    acceptance_criteria: list[str] = Field(min_length=1)


class NonFunctional(Contract):
    id: str
    category: str
    target: str
    verification: str


class Requirements(Contract):
    summary: str
    actors: list[str] = Field(min_length=1)
    functional: list[Requirement] = Field(min_length=1, max_length=12)
    non_functional: list[NonFunctional] = Field(min_length=1, max_length=12)
    assumptions: list[str]
    questions: list[str]
    out_of_scope: list[str]

    @model_validator(mode="after")
    def validate_ids_and_criteria(self):
        for rows in (self.functional, self.non_functional):
            if len({r.id for r in rows}) != len(rows) or any(not r.id.strip() for r in rows):
                raise ValueError("Requirement IDs must be nonempty and unique.")
        for req in self.functional:
            if req.actor not in self.actors:
                raise ValueError("Each functional requirement actor must appear in the actor list.")
            if any(not criterion.strip() for criterion in req.acceptance_criteria):
                raise ValueError("Acceptance criteria must not be empty.")
        return self


class Component(Contract):
    id: str
    name: str
    responsibility: str
    technology: str
    requirement_ids: list[str]


class Decision(Contract):
    title: str
    choice: str
    rationale: str
    tradeoff: str


class Architecture(Contract):
    pattern: str
    components: list[Component] = Field(min_length=1)
    decisions: list[Decision] = Field(min_length=1)
    communication: list[str]
    deployment: str
    security: list[str]


class FieldSpec(Contract):
    name: str
    type: Literal["string", "integer", "number", "boolean", "object", "array"]
    required: bool
    description: str


class Entity(Contract):
    id: str
    name: str
    description: str
    fields: list[FieldSpec] = Field(min_length=1)
    indexes: list[str]
    requirement_ids: list[str]


class Relationship(Contract):
    source: str
    target: str
    cardinality: Literal["one-to-one", "one-to-many", "many-to-many"]
    description: str


class Database(Contract):
    engine: str
    entities: list[Entity] = Field(min_length=1)
    relationships: list[Relationship]


class Endpoint(Contract):
    id: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    summary: str
    authenticated: bool
    request_fields: list[FieldSpec]
    response_fields: list[FieldSpec] = Field(min_length=1)
    success_status: int = Field(ge=200, le=299)
    errors: list[str]
    entity_ids: list[str]
    requirement_ids: list[str]


class APIs(Contract):
    authentication: str
    endpoints: list[Endpoint] = Field(min_length=1)


class Task(Contract):
    id: str
    title: str
    phase: str
    estimate_days: int = Field(ge=1, le=90)
    depends_on: list[str]
    requirement_ids: list[str]
    verification: str


class Implementation(Contract):
    tasks: list[Task] = Field(min_length=1)
    project_structure: list[str]
    risks: list[str]


class Documentation(Contract):
    overview: str
    setup: list[str]
    development_guidelines: list[str]
    testing_strategy: list[str]
    deployment_notes: list[str]


class Finding(Contract):
    rule: str
    severity: Literal["error", "warning"]
    artifact: str
    reference: str
    message: str


class Critique(Contract):
    findings: list[Finding]
    limitations: list[str]
    assessments: list["RequirementAssessment"] = Field(default_factory=list)
    source_assessments: list["SourceAssessment"] = Field(default_factory=list)


class RequirementAssessment(Contract):
    requirement_id: str
    status: Literal["satisfied", "partial", "missing", "uncertain"]
    endpoint_ids: list[str]
    explanation: str = Field(min_length=1)


class SourceAssessment(Contract):
    citation: str
    status: Literal["compliant", "conflict", "not_applicable", "uncertain"]
    requirement_ids: list[str]
    endpoint_ids: list[str]
    explanation: str = Field(min_length=1)


class Blueprint(Contract):
    requirements: Requirements
    architecture: Architecture
    database: Database
    apis: APIs
    implementation: Implementation
    documentation: Documentation


class EditRequirements(Contract):
    expected_etag: str = Field(min_length=64, max_length=64)
    requirements: Requirements


class ImpactInput(Contract):
    requirements: Requirements


class RatingInput(Contract):
    reviewer: str = Field(min_length=2, max_length=100)
    completeness: int = Field(ge=1, le=5)
    correctness: int = Field(ge=1, le=5)
    consistency: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=3000)


class RetrievalQuery(Contract):
    query: str = Field(min_length=3, max_length=2000)
    expected_document_ids: list[str] = Field(min_length=1, max_length=30)


class RetrievalEvaluation(Contract):
    queries: list[RetrievalQuery] = Field(min_length=1, max_length=10)
    k: int = Field(default=4, ge=1, le=10)


SCHEMAS = {
    "requirements": Requirements,
    "architecture": Architecture,
    "database": Database,
    "apis": APIs,
    "implementation": Implementation,
    "documentation": Documentation,
    "critique": Critique,
}
STAGES = list(SCHEMAS)[:-1] + ["validation"]
CreateRun.model_rebuild()
Critique.model_rebuild()


class KnowledgeInput(Contract):
    title: str = Field(min_length=3, max_length=120)
    content: str = Field(min_length=30, max_length=40000)


class SearchInput(Contract):
    query: str = Field(min_length=3, max_length=2000)
