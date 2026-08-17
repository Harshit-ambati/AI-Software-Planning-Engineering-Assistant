import { Clock3, FileText } from "lucide-react";
import type { ProjectSummary } from "../types/workflow";

interface ProjectHistoryProps {
  projects: ProjectSummary[];
  activeProjectId?: string;
  onSelectProject: (projectId: string) => void;
}

export function ProjectHistory({ projects, activeProjectId, onSelectProject }: ProjectHistoryProps) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <Clock3 aria-hidden="true" className="h-5 w-5 text-signal" />
        <div>
          <h2 className="text-base font-semibold text-ink">Project History</h2>
          <p className="mt-1 text-sm text-slate-600">Generated blueprints from this session</p>
        </div>
      </div>

      {projects.length === 0 ? (
        <p className="rounded-lg border border-dashed border-line p-4 text-sm text-slate-500">
          Completed workflows will appear here.
        </p>
      ) : (
        <div className="space-y-2">
          {projects.map((project) => (
            <button
              className={`w-full rounded-lg border p-3 text-left transition hover:border-signal/50 ${
                activeProjectId === project.project_id ? "border-signal bg-blue-50" : "border-line bg-white"
              }`}
              key={project.project_id}
              onClick={() => onSelectProject(project.project_id)}
              type="button"
            >
              <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                <FileText aria-hidden="true" className="h-4 w-4 text-signal" />
                {project.project_id.slice(0, 8)}
              </span>
              <span className="mt-2 line-clamp-2 block text-sm leading-5 text-slate-600">{project.idea}</span>
              <span className="mt-3 inline-flex rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-success">
                {project.validation_status}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
