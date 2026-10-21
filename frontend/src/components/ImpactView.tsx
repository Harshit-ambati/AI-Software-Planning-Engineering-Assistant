import { GitBranch } from 'lucide-react';
import type { Impact } from '../types';
import { human } from '../types';

export default function ImpactView({ impact }: { impact: Impact }) {
  return (
    <div className="impact-result">
      <div className="impact-summary">
        <GitBranch size={20} />
        <strong>
          {impact.added.length} added · {impact.modified.length} modified · {impact.removed.length} removed
        </strong>
      </div>
      {impact.cross_cutting.length > 0 && (
        <p className="note">
          Cross-cutting changes: {impact.cross_cutting.map(human).join(', ')}. All existing design records
          need review.
        </p>
      )}
      {Object.entries(impact.affected).map(([stage, rows]) => (
        <section key={stage} className="artifact-section">
          <h3>
            {human(stage)} · {rows.length} affected
          </h3>
          {rows.length ? (
            rows.map((row) => (
              <div className="impact-record" key={row.id}>
                <code>{row.id}</code>
                <div>
                  <strong>{row.label}</strong>
                  <p>{row.reasons.join('; ')}</p>
                </div>
                <span className="tag">{row.direct ? 'Direct' : 'Dependency'}</span>
              </div>
            ))
          ) : (
            <p className="muted">No linked records affected in this baseline.</p>
          )}
        </section>
      ))}
      {impact.unlinked_new_requirements.length > 0 && (
        <p className="note">
          New requirements need fresh design coverage: {impact.unlinked_new_requirements.join(', ')}.
        </p>
      )}
      {impact.regenerate.length > 0 && (
        <p className="note">Regenerate {impact.regenerate.map(human).join(' and ')} after a change.</p>
      )}
      <div className="note">
        <div>
          {impact.limitations.map((text) => (
            <p key={text}>{text}</p>
          ))}
        </div>
      </div>
    </div>
  );
}
