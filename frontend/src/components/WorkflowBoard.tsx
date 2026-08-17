import { CheckCircle2, Circle, CircleDot, ShieldAlert } from "lucide-react";
import type { WorkflowStage } from "../types/workflow";

interface WorkflowBoardProps {
  stages: WorkflowStage[];
}

const statusIcon = {
  completed: CheckCircle2,
  active: CircleDot,
  pending: Circle,
  blocked: ShieldAlert,
};

const statusClasses = {
  completed: "border-success/30 bg-green-50 text-success",
  active: "border-signal/30 bg-blue-50 text-signal",
  pending: "border-line bg-white text-slate-500",
  blocked: "border-red-200 bg-red-50 text-red-700",
};

export function WorkflowBoard({ stages }: WorkflowBoardProps) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-ink">Engineering Workflow</h2>
          <p className="mt-1 text-sm text-slate-600">Supervisor-led artifact generation pipeline</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        {stages.map((stage) => {
          const Icon = statusIcon[stage.status];

          return (
            <article
              className={`min-h-40 rounded-lg border p-4 ${statusClasses[stage.status]}`}
              key={stage.id}
            >
              <Icon aria-hidden="true" className="mb-4 h-5 w-5" />
              <h3 className="text-sm font-semibold">{stage.label}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{stage.summary}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

