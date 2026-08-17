from enum import StrEnum

from pydantic import BaseModel, Field


class WorkflowStage(StrEnum):
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    API = "api"
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


class DatabaseOutput(BaseModel):
    collections: list[dict] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)


class APIOutput(BaseModel):
    endpoints: list[dict] = Field(default_factory=list)
    authentication: str = ""
    error_cases: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    stage: WorkflowStage
    message: str
    severity: str = "warning"


class ValidationOutput(BaseModel):
    status: str = "PENDING"
    issues: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

