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

