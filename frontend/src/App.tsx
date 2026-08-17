import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Boxes, FileCheck2, GitBranch, Loader2, ShieldCheck } from "lucide-react";
import { ArtifactPanel } from "./components/ArtifactPanel";
import { ProjectHistory } from "./components/ProjectHistory";
import { WorkflowBoard } from "./components/WorkflowBoard";
import { generateBlueprint, getProject, listProjects } from "./lib/api";
import type { ArtifactPreview, EngineeringBlueprint, ProjectSummary, StageStatus, WorkflowStage } from "./types/workflow";

const defaultIdea = "Build an online food delivery application with order tracking and secure payments.";

const baseStages: WorkflowStage[] = [
  {
    id: "requirements",
    label: "Requirements",
    status: "active",
    summary: "Extract actors, functional scope, constraints, and assumptions.",
  },
  {
    id: "architecture",
    label: "Architecture",
    status: "pending",
    summary: "Choose system components, integrations, and deployment shape.",
  },
  {
    id: "database",
    label: "Database",
    status: "pending",
    summary: "Define collections, fields, relationships, and indexes.",
  },
  {
    id: "api",
    label: "API",
    status: "pending",
    summary: "Generate REST endpoints, schemas, auth, and error cases.",
  },
  {
    id: "implementation",
    label: "Plan",
    status: "pending",
    summary: "Break delivery into project structure, phases, and build order.",
  },
  {
    id: "documentation",
    label: "Docs",
    status: "pending",
    summary: "Consolidate artifacts into implementation-ready documentation.",
  },
  {
    id: "validation",
    label: "Validation",
    status: "pending",
    summary: "Check coverage, contradictions, and missing artifact links.",
  },
];

const initialArtifacts: ArtifactPreview[] = [
  {
    title: "Requirement Output",
    stage: "Requirement Agent",
    status: "active",
    items: ["Actors", "Functional requirements", "Non-functional requirements"],
  },
  {
    title: "Architecture Blueprint",
    stage: "Architecture Agent",
    status: "pending",
    items: ["Components", "Technology decisions", "Communication model"],
  },
  {
    title: "Validation Report",
    stage: "Validation Agent",
    status: "pending",
    items: ["Requirement coverage", "Schema/API consistency", "Recommendations"],
  },
];

function getStages(blueprint: EngineeringBlueprint | null, loading: boolean): WorkflowStage[] {
  if (loading) {
    return baseStages.map((stage, index) => ({
      ...stage,
      status: index === 0 ? "active" : "pending",
    }));
  }

  if (!blueprint) {
    return baseStages;
  }

  const validationStatus: StageStatus = blueprint.validation.status === "PASS" ? "completed" : "blocked";
  return baseStages.map((stage) => ({
    ...stage,
    status: stage.id === "validation" ? validationStatus : "completed",
  }));
}

function getArtifacts(blueprint: EngineeringBlueprint | null, loading: boolean): ArtifactPreview[] {
  if (!blueprint) {
    return loading
      ? initialArtifacts.map((artifact, index) => ({
          ...artifact,
          status: index === 0 ? "active" : "pending",
        }))
      : initialArtifacts;
  }

  return [
    {
      title: "Requirement Output",
      stage: "Requirement Agent",
      status: "completed",
      items: [
        `${blueprint.requirements.actors.length} actors identified`,
        `${blueprint.requirements.functional_requirements.length} functional requirements`,
        `${blueprint.requirements.non_functional_requirements.length} non-functional requirements`,
      ],
    },
    {
      title: "Architecture Blueprint",
      stage: "Architecture Agent",
      status: "completed",
      items: [
        blueprint.architecture.architecture_pattern,
        `${blueprint.architecture.components.length} components`,
        `${blueprint.architecture.decisions.length} technology decisions`,
      ],
    },
    {
      title: "Database Schema",
      stage: "Database Agent",
      status: "completed",
      items: blueprint.database.collections.map((collection) => `${collection.name}: ${collection.description}`),
    },
    {
      title: "API Specification",
      stage: "API Agent",
      status: "completed",
      items: blueprint.api.endpoints.map((endpoint) => `${endpoint.method} ${endpoint.path}`),
    },
    {
      title: "Implementation Plan",
      stage: "Documentation Agent",
      status: "completed",
      items: blueprint.implementation.phases,
    },
    {
      title: "Validation Report",
      stage: "Validation Agent",
      status: blueprint.validation.status === "PASS" ? "completed" : "blocked",
      items:
        blueprint.validation.issues.length > 0
          ? blueprint.validation.issues.map((issue) => issue.message)
          : blueprint.validation.recommendations,
    },
  ];
}

function App() {
  const [idea, setIdea] = useState(defaultIdea);
  const [blueprint, setBlueprint] = useState<EngineeringBlueprint | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stages = useMemo(() => getStages(blueprint, loading), [blueprint, loading]);
  const artifacts = useMemo(() => getArtifacts(blueprint, loading), [blueprint, loading]);

  const refreshProjects = useCallback(async () => {
    try {
      const result = await listProjects();
      setProjects(result);
    } catch {
      setProjects([]);
    }
  }, []);

  useEffect(() => {
    refreshProjects();
  }, [refreshProjects]);

  async function handleStartWorkflow() {
    setLoading(true);
    setError(null);

    try {
      const result = await generateBlueprint(idea);
      setBlueprint(result);
      await refreshProjects();
    } catch {
      setError("The backend workflow is not reachable yet. Start it with Docker Compose or FastAPI, then try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectProject(projectId: string) {
    setHistoryLoading(true);
    setError(null);

    try {
      const result = await getProject(projectId);
      setBlueprint(result);
      setIdea(result.idea);
    } catch {
      setError("Unable to load that project blueprint from the backend.");
    } finally {
      setHistoryLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium text-signal">AI Engineering Assistant</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">Software Planning Workspace</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            <span className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2">
              <Activity aria-hidden="true" className="h-4 w-4 text-success" />
              MVP workflow
            </span>
            <span className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2">
              <ShieldCheck aria-hidden="true" className="h-4 w-4 text-signal" />
              Validation-first
            </span>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6">
        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <Boxes aria-hidden="true" className="h-5 w-5 text-signal" />
            <p className="mt-4 text-sm text-slate-500">Active project</p>
            <p className="mt-1 text-lg font-semibold">{blueprint ? blueprint.project_id.slice(0, 8) : "Blueprint Generator"}</p>
          </div>
          <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <GitBranch aria-hidden="true" className="h-5 w-5 text-caution" />
            <p className="mt-4 text-sm text-slate-500">Current agent</p>
            <p className="mt-1 text-lg font-semibold">{loading ? "Supervisor" : blueprint ? "Complete" : "Ready"}</p>
          </div>
          <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <FileCheck2 aria-hidden="true" className="h-5 w-5 text-success" />
            <p className="mt-4 text-sm text-slate-500">Validation status</p>
            <p className="mt-1 text-lg font-semibold">{blueprint ? blueprint.validation.status : "Waiting for artifacts"}</p>
          </div>
        </section>

        <WorkflowBoard stages={stages} />

        <div className="grid gap-5 xl:grid-cols-[280px_1fr_380px]">
          <ProjectHistory
            activeProjectId={blueprint?.project_id}
            onSelectProject={handleSelectProject}
            projects={projects}
          />

          <div className="grid gap-5">
            <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
              <h2 className="text-base font-semibold text-ink">Project Intake</h2>
              <textarea
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                className="mt-4 min-h-44 w-full resize-none rounded-lg border border-line bg-white p-4 text-sm leading-6 outline-none ring-signal/20 transition focus:ring-4"
                placeholder="Describe a software idea, for example: Build an online food delivery application."
              />
              {error ? <p className="mt-3 text-sm font-medium text-red-700">{error}</p> : null}
              {blueprint ? (
                <div className="mt-4 rounded-lg border border-line bg-panel p-4 text-sm leading-6 text-slate-700">
                  <p className="font-semibold text-ink">{blueprint.documentation.overview}</p>
                  <p className="mt-2">{blueprint.architecture.architecture_pattern}</p>
                </div>
              ) : null}
              <div className="mt-4 flex justify-end">
                <button
                  className="inline-flex items-center gap-2 rounded-lg bg-signal px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                  disabled={loading || historyLoading || idea.trim().length < 10}
                  onClick={handleStartWorkflow}
                  type="button"
                >
                  {loading ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
                  {loading ? "Running" : "Start Workflow"}
                </button>
              </div>
            </section>
          </div>

          <ArtifactPanel artifacts={artifacts} />
        </div>
      </div>
    </main>
  );
}

export default App;
