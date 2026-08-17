export type StageStatus = "completed" | "active" | "pending" | "blocked";

export interface WorkflowStage {
  id: string;
  label: string;
  status: StageStatus;
  summary: string;
}

export interface ArtifactPreview {
  title: string;
  stage: string;
  status: StageStatus;
  items: string[];
}

export interface ValidationIssue {
  stage: string;
  message: string;
  severity: string;
}

export interface EngineeringBlueprint {
  project_id: string;
  idea: string;
  requirements: {
    actors: string[];
    functional_requirements: string[];
    non_functional_requirements: string[];
    assumptions: string[];
    constraints: string[];
  };
  architecture: {
    components: string[];
    technologies: string[];
    architecture_pattern: string;
    communication: string[];
    decisions: string[];
  };
  database: {
    collections: Array<{
      name: string;
      description: string;
      fields: string[];
    }>;
    relationships: string[];
    indexes: string[];
  };
  api: {
    endpoints: Array<{
      method: string;
      path: string;
      description: string;
      authentication_required: boolean;
    }>;
    authentication: string;
    error_cases: string[];
  };
  implementation: {
    project_structure: string[];
    phases: string[];
    dependencies: string[];
    suggested_order: string[];
  };
  documentation: {
    overview: string;
    setup_instructions: string[];
    architecture_notes: string[];
    api_notes: string[];
    development_guidelines: string[];
  };
  validation: {
    status: "PASS" | "FAIL" | "PENDING";
    issues: ValidationIssue[];
    warnings: string[];
    recommendations: string[];
  };
}

export interface ProjectSummary {
  project_id: string;
  idea: string;
  status: string;
  validation_status: string;
  created_at: string;
}
