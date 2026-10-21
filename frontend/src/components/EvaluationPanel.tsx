import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowDownToLine, FlaskConical, Plus } from 'lucide-react';
import { api } from '../api';
import type { Knowledge, Project, RetrievalResult, Run, RunMetrics } from '../types';
import { human, isActive } from '../types';

type Scorecard = { runs: RunMetrics[]; retrieval: RetrievalResult[] };
export default function EvaluationPanel({
  project,
  run,
  onStart,
  onSelect,
}: {
  project: Project;
  run: Run | null;
  onStart: (strategy: 'staged' | 'single_prompt', memory: boolean) => Promise<void>;
  onSelect: (id: string) => void;
}) {
  const [data, setData] = useState<Scorecard>({ runs: [], retrieval: [] });
  const [docs, setDocs] = useState<Knowledge[]>([]);
  const [mode, setMode] = useState('all');
  const [strategy, setStrategy] = useState<'staged' | 'single_prompt'>('single_prompt');
  const [memory, setMemory] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reviewer, setReviewer] = useState('');
  const [scores, setScores] = useState({ completeness: 3, correctness: 3, consistency: 3 });
  const [notes, setNotes] = useState('');
  const [k, setK] = useState(4);
  const [queries, setQueries] = useState([{ query: '', expected_document_ids: [] as string[] }]);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api<Scorecard>(`/projects/${project.id}/evaluations`, undefined, controller.signal),
      api<Knowledge[]>(`/projects/${project.id}/knowledge`, undefined, controller.signal),
    ])
      .then(([values, library]) => {
        setData(values);
        setDocs(library);
        setLoading(false);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [project.id, run?.id, run?.status, reload]);
  async function start() {
    setBusy(true);
    setError('');
    try {
      await onStart(strategy, memory);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function rate(event: FormEvent) {
    event.preventDefault();
    if (!run) return;
    setBusy(true);
    setError('');
    try {
      await api(`/runs/${run.id}/evaluation/ratings`, { reviewer, ...scores, notes });
      setReload((n) => n + 1);
      setNotes('');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function retrieve(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api(`/projects/${project.id}/evaluation/retrieval`, { queries, k });
      setReload((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function exportMetrics() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'project-evaluation.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const rows = data.runs.filter((row) => mode === 'all' || (mode === 'live' ? row.is_live : !row.is_live));
  const active = project.runs?.some((r) => isActive(r.status) || r.status === 'awaiting_review');
  if (loading)
    return (
      <section className="panel">
        <div className="empty-inline">
          <span className="spinner" />
          Loading evaluation measurements…
        </div>
      </section>
    );
  return (
    <>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">MEASURE THE ENGINEERING PROCESS</span>
            <h2>Evaluation workbench</h2>
            <p>Compare generation strategies, collect ratings and test retrieval.</p>
          </div>
          <button className="secondary" onClick={exportMetrics}>
            <ArrowDownToLine size={15} />
            Export measurements
          </button>
        </div>
        <div className="note">
          <FlaskConical size={18} />
          <div>
            <strong>Measurements, not a claim of design accuracy.</strong>
            <p>
              Demo runs are fixed fixtures. Linked coverage measures references. Semantic coverage is an
              automated reviewer judgment. Human ratings use a 1–5 rubric. Compare matching briefs,
              constraints and source sets; review edits are a confounder.
            </p>
          </div>
        </div>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
        <div className="experiment-controls">
          <label>
            Generation strategy
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as 'staged' | 'single_prompt')}
            >
              <option value="single_prompt">Single-prompt baseline</option>
              <option value="staged">Specialized agent workflow</option>
            </select>
          </label>
          <label>
            Project knowledge
            <select value={String(memory)} onChange={(e) => setMemory(e.target.value === 'true')}>
              <option value="false">Without retrieval</option>
              <option value="true">With retrieval</option>
            </select>
          </label>
          <button className="primary" disabled={busy || active} onClick={() => void start()}>
            <Plus size={15} />
            Start comparison run
          </button>
        </div>
        <p className="muted evaluation-caption">
          Uses this revision’s brief and constraints. Baseline generation skips human review; staged runs
          pause for approval. Live mode consumes provider quota.
        </p>
        <label className="metric-filter">
          Show measurements
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="all">All (clearly labeled)</option>
            <option value="live">Live only</option>
            <option value="demo">Demo only</option>
          </select>
        </label>
        <div className="table-scroll">
          <table className="evaluation-table">
            <thead>
              <tr>
                <th>Revision / mode</th>
                <th>Strategy</th>
                <th>Generation time</th>
                <th>Tokens in / out / reasoning</th>
                <th>Coverage linked / semantic</th>
                <th>Human ratings</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <button className="text-button" onClick={() => onSelect(row.id)}>
                      Revision {row.version}
                    </button>
                    <span className="tag">{row.is_live ? 'LIVE' : 'DEMO'}</span>
                    <small>{human(row.status)}</small>
                  </td>
                  <td>
                    {human(row.strategy)}
                    <small>{row.use_memory ? 'With retrieval' : 'No retrieval'}</small>
                    <small>{row.model}</small>
                    <small>
                      Scope {row.scope_hash?.slice(0, 8)} · Sources {row.sources_hash?.slice(0, 8)}
                    </small>
                    {(row.human_edited || row.human_seeded) && (
                      <small>
                        {row.human_edited ? 'Human-edited requirements' : 'Human-seeded requirements'}
                      </small>
                    )}
                  </td>
                  <td>
                    {(row.generation_ms / 1000).toFixed(2)} s
                    <small>{row.wall_seconds.toFixed(1)} s wall incl. review</small>
                    <small>{row.model_attempts} model attempts</small>
                  </td>
                  <td>
                    {row.input_tokens} / {row.output_tokens} / {row.reasoning_tokens}
                    <small>{row.prompt_versions.join(', ') || 'Not generated'}</small>
                  </td>
                  <td>
                    {row.linked_coverage === null ? '—' : `${row.linked_coverage}%`} /{' '}
                    {row.semantic_coverage === null ? 'Not assessed' : `${row.semantic_coverage}%`}
                  </td>
                  <td>
                    {row.human_review_count
                      ? Object.entries(row.human_scores).map(([key, value]) => (
                          <small key={key}>
                            {human(key)}: {value}/5
                          </small>
                        ))
                      : 'Unrated'}
                    <small>{row.human_review_count} reviews</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <p className="muted">No runs match this measurement filter.</p>}
        <p className="evaluation-caption muted">
          Telemetry covers completed model stages. Embedding time and failed-stage usage may be absent;
          generation time excludes queueing and review. Raw JSON exports preserve the measurement limitations.
        </p>
        {run && ['passed', 'needs_attention'].includes(run.status) && (
          <form className="rating-form" onSubmit={rate}>
            <h3>Rate revision {run.version}</h3>
            <p className="muted evaluation-caption">
              1 = major gaps · 3 = usable with corrections · 5 = meets the brief without material issues.
              Inspect the artifacts before rating.
            </p>
            <div className="edit-columns">
              <label>
                Reviewer name
                <input
                  value={reviewer}
                  minLength={2}
                  maxLength={100}
                  required
                  onChange={(e) => setReviewer(e.target.value)}
                />
              </label>
              {(Object.keys(scores) as (keyof typeof scores)[]).map((key) => (
                <label key={key}>
                  {human(key)}
                  <select
                    value={scores[key]}
                    onChange={(e) => setScores({ ...scores, [key]: Number(e.target.value) })}
                  >
                    {[1, 2, 3, 4, 5].map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            <label>
              Review evidence / notes
              <textarea rows={2} value={notes} maxLength={3000} onChange={(e) => setNotes(e.target.value)} />
            </label>
            <button className="secondary" disabled={busy}>
              Save human rating
            </button>
          </form>
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Retrieval quality</h2>
            <p>Define expected documents before running the queries.</p>
          </div>
        </div>
        {docs.length ? (
          <form onSubmit={retrieve}>
            <label>
              Top k
              <input
                type="number"
                min={1}
                max={10}
                required
                value={k}
                onChange={(e) => setK(Number(e.target.value))}
              />
            </label>
            {queries.map((item, index) => (
              <fieldset className="retrieval-query" key={index}>
                <legend>Query {index + 1}</legend>
                <label>
                  Search query
                  <input
                    required
                    minLength={3}
                    maxLength={2000}
                    value={item.query}
                    onChange={(e) =>
                      setQueries(queries.map((q, i) => (i === index ? { ...q, query: e.target.value } : q)))
                    }
                  />
                </label>
                <span className="section-label">EXPECTED RELEVANT DOCUMENTS</span>
                {docs.map((doc) => (
                  <label className="checkbox-label" key={doc.id}>
                    <input
                      type="checkbox"
                      checked={item.expected_document_ids.includes(doc.id)}
                      onChange={(e) =>
                        setQueries(
                          queries.map((q, i) =>
                            i === index
                              ? {
                                  ...q,
                                  expected_document_ids: e.target.checked
                                    ? [...q.expected_document_ids, doc.id]
                                    : q.expected_document_ids.filter((id) => id !== doc.id),
                                }
                              : q,
                          ),
                        )
                      }
                    />
                    {doc.title}
                  </label>
                ))}
                {queries.length > 1 && (
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => setQueries(queries.filter((_, i) => i !== index))}
                  >
                    Remove query
                  </button>
                )}
              </fieldset>
            ))}
            <div className="form-footer">
              <button
                type="button"
                className="secondary"
                disabled={queries.length >= 10}
                onClick={() => setQueries([...queries, { query: '', expected_document_ids: [] }])}
              >
                Add query
              </button>
              <button
                className="primary"
                disabled={busy || queries.some((q) => !q.expected_document_ids.length)}
              >
                Evaluate retrieval
              </button>
            </div>
          </form>
        ) : (
          <div className="empty-inline">
            <h3>Add source documents first.</h3>
            <p>The Knowledge tab holds the project’s evaluation corpus.</p>
          </div>
        )}
        {data.retrieval.map((record) => (
          <details className="source-card retrieval-score" key={record.id}>
            <summary>
              <strong>
                {record.result.mode} · {record.result.query_count} queries
              </strong>
              <span>
                P@{record.result.k}: {record.result.precision_at_k.toFixed(3)} · Recall:{' '}
                {record.result.recall_at_k.toFixed(3)} · MRR: {record.result.mrr.toFixed(3)}
              </span>
            </summary>
            <p>{record.result.definition}</p>
            {record.result.queries.map((q, i) => (
              <div key={i}>
                <strong>{q.query}</strong>
                <p>
                  P@k {q.precision_at_k} · Recall {q.recall_at_k} · Reciprocal rank {q.reciprocal_rank}
                </p>
                <ul>
                  {q.retrieved.map((hit) => (
                    <li key={hit.citation}>
                      {hit.title} · similarity {hit.score.toFixed(3)}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </details>
        ))}
      </section>
    </>
  );
}
