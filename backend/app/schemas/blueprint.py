from enum import StrEnum
from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowStage(StrEnum):
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    API = "api"
    IMPLEMENTATION = "implementation"
    DOCUMENTATION = "documentation"
    VALIDATION = "validation"


class RequirementOutput(BaseModel):
    actors: list[str] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class ArchitectureOutput(BaseModel):
    components: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    architecture_pattern: str = ""
    communication: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)


class TechnologyDecision(BaseModel):
    name: str
    purpose: str
    rationale: str


class DatabaseCollection(BaseModel):
    name: str
    description: str
    fields: list[str] = Field(default_factory=list)


class DatabaseOutput(BaseModel):
    collections: list[DatabaseCollection] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)


class APIEndpoint(BaseModel):
    method: str
    path: str
    description: str
    request_schema: dict = Field(default_factory=dict)
    response_schema: dict = Field(default_factory=dict)
    authentication_required: bool = True


class APIOutput(BaseModel):
    endpoints: list[APIEndpoint] = Field(default_factory=list)
    authentication: str = ""
    error_cases: list[str] = Field(default_factory=list)


class ImplementationOutput(BaseModel):
    project_structure: list[str] = Field(default_factory=list)
    phases: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    suggested_order: list[str] = Field(default_factory=list)


class DocumentationOutput(BaseModel):
    overview: str
    setup_instructions: list[str] = Field(default_factory=list)
    architecture_notes: list[str] = Field(default_factory=list)
    api_notes: list[str] = Field(default_factory=list)
    development_guidelines: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    stage: WorkflowStage
    message: str
    severity: str = "warning"


class ValidationOutput(BaseModel):
    status: str = "PENDING"
    issues: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class BlueprintRequest(BaseModel):
    idea: str = Field(min_length=10, max_length=5000)


class EngineeringBlueprint(BaseModel):
    project_id: str
    idea: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    requirements: RequirementOutput
    architecture: ArchitectureOutput
    database: DatabaseOutput
    api: APIOutput
    implementation: ImplementationOutput
    documentation: DocumentationOutput
    validation: ValidationOutput


class ProjectSummary(BaseModel):
    project_id: str
    idea: str
    status: str
    validation_status: str
    created_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectSummary] = Field(default_factory=list)
