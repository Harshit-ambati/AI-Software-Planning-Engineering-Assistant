import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { GitBranch, Plus, Save, Trash2, X } from 'lucide-react';
import { api } from '../api';
import type { Impact, Requirement, Requirements, Run } from '../types';
import ImpactView from './ImpactView';

export default function RequirementsEditor({
  run,
  mode,
  onClose,
  onSaved,
  onCreate,
}: {
  run: Run;
  mode: 'edit' | 'impact';
  onClose: () => void;
  onSaved: (run: Run) => void;
  onCreate: (requirements: Requirements) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<Requirements>(() =>
    structuredClone(run.artifacts.requirements as unknown as Requirements),
  );
  const [etag] = useState(run.requirements_etag);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  function change(next: Requirements) {
    setDraft(next);
    setImpact(null);
  }
  function update(index: number, patch: Partial<Requirement>) {
    change({ ...draft, functional: draft.functional.map((r, i) => (i === index ? { ...r, ...patch } : r)) });
  }
  async function analyze() {
    setBusy(true);
    setError('');
    try {
      setImpact(await api<Impact>(`/runs/${run.id}/analysis/impact`, { requirements: draft }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (mode === 'edit') {
        onSaved(
          await api<Run>(`/runs/${run.id}/review/requirements`, { requirements: draft, expected_etag: etag }),
        );
      } else {
        await onCreate(draft);
      }
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function add() {
    let i = 1;
    while (draft.functional.some((r) => r.id === `FR-${i}`)) i++;
    change({
      ...draft,
      functional: [
        ...draft.functional,
        {
          id: `FR-${i}`,
          title: '',
          description: '',
          actor: draft.actors[0] || '',
          priority: 'must',
          acceptance_criteria: [''],
        },
      ],
    });
  }
  return (
    <dialog
      ref={dialog}
      className="requirements-dialog"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
    >
      <div className="modal-heading">
        <div>
          <span className="eyebrow">HUMAN ENGINEERING REVIEW</span>
          <h2>{mode === 'edit' ? 'Edit requirements before approval' : 'Explore the impact of a change'}</h2>
        </div>
        <button
          disabled={busy}
          className="icon-button"
          aria-label="Close requirement editor"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      <div className="note">
        {mode === 'edit'
          ? 'Saved edits are audited. Approving this revision sends the edited scope to all downstream agents.'
          : 'This is a proposal against the selected revision. Analyze changes before creating a new revision; the baseline stays unchanged.'}
      </div>
      <form onSubmit={save}>
        <label>
          Summary
          <textarea
            rows={2}
            value={draft.summary}
            required
            onChange={(e) => change({ ...draft, summary: e.target.value })}
          />
        </label>
        <label>
          Actors (comma separated)
          <input
            required
            value={draft.actors.join(', ')}
            onChange={(e) => change({ ...draft, actors: e.target.value.split(',').map((s) => s.trim()) })}
          />
        </label>
        {draft.functional.map((req, index) => (
          <fieldset className="requirement-edit" key={req.id}>
            <legend>{req.id}</legend>
            <div className="edit-heading">
              <strong>Functional requirement</strong>
              <button
                type="button"
                className="icon-button"
                aria-label={`Remove ${req.id}`}
                disabled={busy || draft.functional.length === 1}
                onClick={() =>
                  change({ ...draft, functional: draft.functional.filter((_, i) => i !== index) })
                }
              >
                <Trash2 size={16} />
              </button>
            </div>
            <label>
              Title
              <input
                required
                maxLength={200}
                value={req.title}
                onChange={(e) => update(index, { title: e.target.value })}
              />
            </label>
            <label>
              Description
              <textarea
                required
                maxLength={3000}
                rows={2}
                value={req.description}
                onChange={(e) => update(index, { description: e.target.value })}
              />
            </label>
            <div className="edit-columns">
              <label>
                Actor
                <select value={req.actor} onChange={(e) => update(index, { actor: e.target.value })}>
                  {draft.actors.map((actor, i) => (
                    <option key={i} value={actor}>
                      {actor || 'Enter an actor'}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Priority
                <select
                  value={req.priority}
                  onChange={(e) => update(index, { priority: e.target.value as Requirement['priority'] })}
                >
                  {['must', 'should', 'could'].map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Acceptance criteria (one per line)
              <textarea
                required
                rows={3}
                value={req.acceptance_criteria.join('\n')}
                onChange={(e) => update(index, { acceptance_criteria: e.target.value.split('\n') })}
              />
            </label>
          </fieldset>
        ))}
        <button
          type="button"
          className="secondary"
          disabled={busy || draft.functional.length >= 12}
          onClick={add}
        >
          <Plus size={15} />
          Add requirement
        </button>
        <details className="context-editor">
          <summary>Quality requirements and scope details</summary>
          {draft.non_functional.map((nfr, index) => (
            <fieldset className="requirement-edit" key={nfr.id}>
              <legend>{nfr.id}</legend>
              {(['category', 'target', 'verification'] as const).map((key) => (
                <label key={key}>
                  {key}
                  <input
                    required
                    value={nfr[key]}
                    onChange={(e) =>
                      change({
                        ...draft,
                        non_functional: draft.non_functional.map((r, i) =>
                          i === index ? { ...r, [key]: e.target.value } : r,
                        ),
                      })
                    }
                  />
                </label>
              ))}
            </fieldset>
          ))}
          {(['assumptions', 'questions', 'out_of_scope'] as const).map((key) => (
            <label key={key}>
              {key.replaceAll('_', ' ')} (one per line)
              <textarea
                rows={2}
                value={draft[key].join('\n')}
                onChange={(e) => change({ ...draft, [key]: e.target.value.split('\n').filter(Boolean) })}
              />
            </label>
          ))}
        </details>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
        {impact && <ImpactView impact={impact} />}
        <div className="form-footer">
          <button type="button" className="secondary" disabled={busy} onClick={() => void analyze()}>
            <GitBranch size={15} />
            Analyze impact
          </button>
          <button className="primary" disabled={busy}>
            {mode === 'edit' ? <Save size={15} /> : <Plus size={15} />}{' '}
            {busy ? 'Working…' : mode === 'edit' ? 'Save requirements' : 'Create revised blueprint'}
          </button>
        </div>
      </form>
    </dialog>
  );
}
