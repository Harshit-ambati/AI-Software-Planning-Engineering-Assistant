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
}
export const isActive = (status?: string) => status === 'running' || status === 'queued';
export const human = (value: string) => value.replaceAll('_', ' ').replace(/^\w/, (c) => c.toUpperCase());
