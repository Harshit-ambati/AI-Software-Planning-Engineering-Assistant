import { Activity, Boxes, FileCheck2, GitBranch, ShieldCheck } from "lucide-react";
import { ArtifactPanel } from "./components/ArtifactPanel";
import { WorkflowBoard } from "./components/WorkflowBoard";
import type { ArtifactPreview, WorkflowStage } from "./types/workflow";

const stages: WorkflowStage[] = [
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

const artifacts: ArtifactPreview[] = [
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

function App() {
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
              Milestone 1
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
            <p className="mt-1 text-lg font-semibold">Blueprint Generator</p>
          </div>
          <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <GitBranch aria-hidden="true" className="h-5 w-5 text-caution" />
            <p className="mt-4 text-sm text-slate-500">Current agent</p>
            <p className="mt-1 text-lg font-semibold">Requirement Agent</p>
          </div>
          <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <FileCheck2 aria-hidden="true" className="h-5 w-5 text-success" />
            <p className="mt-4 text-sm text-slate-500">Validation status</p>
            <p className="mt-1 text-lg font-semibold">Waiting for artifacts</p>
          </div>
        </section>

        <WorkflowBoard stages={stages} />

        <div className="grid gap-5 lg:grid-cols-[1fr_380px]">
          <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-ink">Project Intake</h2>
            <textarea
              className="mt-4 min-h-44 w-full resize-none rounded-lg border border-line bg-white p-4 text-sm leading-6 outline-none ring-signal/20 transition focus:ring-4"
              placeholder="Describe a software idea, for example: Build an online food delivery application."
            />
            <div className="mt-4 flex justify-end">
              <button className="rounded-lg bg-signal px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700">
                Start Workflow
              </button>
            </div>
          </section>

          <ArtifactPanel artifacts={artifacts} />
        </div>
      </div>
    </main>
  );
}

export default App;

