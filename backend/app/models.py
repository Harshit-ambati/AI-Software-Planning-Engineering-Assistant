from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class Requirement(Contract):
    id: str
    title: str
    description: str
    actor: str
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
    functional: list[Requirement] = Field(min_length=1)
    non_functional: list[NonFunctional] = Field(min_length=1)
    assumptions: list[str]
    questions: list[str]
    out_of_scope: list[str]


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


class KnowledgeInput(Contract):
    title: str = Field(min_length=3, max_length=120)
    content: str = Field(min_length=30, max_length=40000)


class SearchInput(Contract):
    query: str = Field(min_length=3, max_length=2000)
