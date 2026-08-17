import type { ArtifactPreview } from "../types/workflow";

interface ArtifactPanelProps {
  artifacts: ArtifactPreview[];
}

const badgeClasses = {
  completed: "bg-green-100 text-success",
  active: "bg-blue-100 text-signal",
  pending: "bg-slate-100 text-slate-600",
  blocked: "bg-red-100 text-red-700",
};

export function ArtifactPanel({ artifacts }: ArtifactPanelProps) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="text-base font-semibold text-ink">Artifact Views</h2>
        <p className="mt-1 text-sm text-slate-600">Structured outputs will appear here as agents complete.</p>
      </div>

      <div className="space-y-3">
        {artifacts.map((artifact) => (
          <article className="rounded-lg border border-line p-4" key={artifact.title}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-ink">{artifact.title}</h3>
                <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{artifact.stage}</p>
              </div>
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${badgeClasses[artifact.status]}`}>
                {artifact.status}
              </span>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              {artifact.items.map((item) => (
                <li className="border-l-2 border-line pl-3" key={item}>
                  {item}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

