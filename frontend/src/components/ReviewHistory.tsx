import { useState } from 'react';
import { api } from '../api';
import type { Json } from '../types';
import { ValueView } from './ArtifactView';

interface Edit {
  id: number;
  created_at: string;
  old_hash: string;
  new_hash: string;
  before_content: Json;
  after_content: Json;
}
export default function ReviewHistory({ runId }: { runId: string }) {
  const [rows, setRows] = useState<Edit[] | null>(null);
  const [error, setError] = useState('');
  async function load() {
    try {
      setRows(await api<Edit[]>(`/runs/${runId}/review/history`));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <details
      className="source-card"
      onToggle={(e) => {
        if (e.currentTarget.open && rows === null) void load();
      }}
    >
      <summary>Requirement edit audit trail</summary>
      {error && <p role="alert">{error}</p>}
      {rows === null ? (
        <p className="muted">Loading saved edits…</p>
      ) : rows.length === 0 ? (
        <p className="muted">No requirements were edited during this revision’s review.</p>
      ) : (
        rows.map((row) => (
          <details key={row.id}>
            <summary>
              {new Date(row.created_at).toLocaleString()} · {row.old_hash.slice(0, 8)} →{' '}
              {row.new_hash.slice(0, 8)}
            </summary>
            <div className="diff-columns">
              <div>
                <small>BEFORE</small>
                <ValueView value={row.before_content} />
              </div>
              <div>
                <small>AFTER</small>
                <ValueView value={row.after_content} />
              </div>
            </div>
          </details>
        ))
      )}
    </details>
  );
}
