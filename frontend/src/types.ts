export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export type Stage =
  'requirements' | 'architecture' | 'database' | 'apis' | 'implementation' | 'documentation' | 'validation';
export const stages: Stage[] = [
  'requirements',
  'architecture',
  'database',
  'apis',
  'implementation',
  'documentation',
  'validation',
];
export const labels: Record<Stage, string> = {
  requirements: 'Requirements',
  architecture: 'Architecture',
  database: 'Database',
  apis: 'API design',
  implementation: 'Implementation',
  documentation: 'Documentation',
  validation: 'Validation',
};
export interface Event {
  id: number;
  stage: string;
  status: string;
  created_at: string;
  detail: Record<string, Json>;
}
export interface Run {
  id: string;
  project_id: string;
  version: number;
  brief: string;
  constraints_text: string;
  provider: string;
  model: string;
  status: string;
  created_at: string;
  error: string | null;
  artifacts: Partial<Record<Stage | 'sources' | 'critique', Json>>;
  events: Event[];
  requirements_etag?: string;
  strategy?: 'staged' | 'single_prompt';
  use_memory?: boolean;
  parent_run_id?: string | null;
}
export interface Project {
  id: string;
  name: string;
  brief: string;
  constraints_text: string;
  created_at: string;
  status?: string;
  run_count?: number;
  runs?: Run[];
}
export interface Config {
  provider: string;
  model: string;
  live_ready: boolean;
  memory: string;
}
export interface Finding {
  rule: string;
  severity: string;
  artifact: string;
  reference: string;
  message: string;
}
export interface Coverage {
  requirement_id: string;
  title: string;
  architecture: string[];
  database: string[];
  apis: string[];
  implementation: string[];
}
export interface Report {
  status: string;
  coverage_percent: number;
  findings: Finding[];
  coverage: Coverage[];
  limitations: string[];
  semantic_coverage_percent?: number | null;
  semantic_assessments?: {
    requirement_id: string;
    status: string;
    endpoint_ids: string[];
    explanation: string;
  }[];
  source_assessments?: {
    citation: string;
    status: string;
    requirement_ids: string[];
    endpoint_ids: string[];
    explanation: string;
  }[];
}
export interface Knowledge {
  id: string;
  title: string;
  content: string;
  created_at: string;
}
export interface Hit {
  citation: string;
  title: string;
  text: string;
  score: number;
}
export interface Diff {
  before_version: number;
  after_version: number;
  brief_changed: boolean;
  changes: { path: string; before: Json; after: Json }[];
  impact?: Impact;
}
export interface Requirement {
  id: string;
  title: string;
  description: string;
  actor: string;
  priority: 'must' | 'should' | 'could';
  acceptance_criteria: string[];
}
export interface Requirements {
  summary: string;
  actors: string[];
  functional: Requirement[];
  non_functional: { id: string; category: string; target: string; verification: string }[];
  assumptions: string[];
  questions: string[];
  out_of_scope: string[];
}
export interface Impact {
  added: string[];
  removed: string[];
  modified: string[];
  cross_cutting: string[];
  affected: Record<string, { id: string; label: string; reasons: string[]; direct: boolean }[]>;
  regenerate: string[];
  unlinked_new_requirements: string[];
  limitations: string[];
}
export interface RunMetrics {
  scope_hash: string;
  sources_hash: string;
  human_edited: boolean;
  human_seeded: boolean;
  id: string;
  version: number;
  provider: string;
  model: string;
  strategy: string;
  status: string;
  is_live: boolean;
  use_memory: boolean;
  brief_hash: string;
  generation_ms: number;
  wall_seconds: number;
  input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  model_attempts: number;
  linked_coverage: number | null;
  semantic_coverage: number | null;
  findings: number;
  human_scores: Record<string, number | null>;
  human_review_count: number;
  prompt_versions: string[];
  limitations: string[];
}
export interface RetrievalResult {
  id: string;
  created_at: string;
  result: {
    mode: string;
    k: number;
    query_count: number;
    precision_at_k: number;
    recall_at_k: number;
    mrr: number;
    definition: string;
    queries: {
      query: string;
      precision_at_k: number;
      recall_at_k: number;
      reciprocal_rank: number;
      retrieved: Hit[];
    }[];
  };
}
export const isActive = (status?: string) => status === 'running' || status === 'queued';
export const human = (value: string) => value.replaceAll('_', ' ').replace(/^\w/, (c) => c.toUpperCase());
