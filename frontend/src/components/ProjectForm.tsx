import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowRight, Sparkles, X } from 'lucide-react';
import type { Project } from '../types';

const demoBrief =
  'Build a food delivery platform where customers browse restaurants, place orders, track delivery and cancel before preparation. Restaurant managers maintain menus and couriers update delivery status.';

export default function ProjectForm({
  project,
  demo,
  onClose,
  onSubmit,
}: {
  project?: Project;
  demo: boolean;
  onClose: () => void;
  onSubmit: (name: string, brief: string, constraints: string) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [name, setName] = useState(project?.name || '');
  const [brief, setBrief] = useState(project?.brief || '');
  const [constraints, setConstraints] = useState(project?.constraints_text || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await onSubmit(name, brief, constraints);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Could not create project.');
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="project-dialog"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else onClose();
      }}
    >
      <div className="modal-heading">
        <div>
          <span className="eyebrow">START WITH AN IDEA</span>
          <h2>{project ? 'Create a new revision' : 'Your next engineering blueprint'}</h2>
        </div>
        <button className="icon-button" aria-label="Close dialog" disabled={busy} onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      <p className="muted">Define the problem. The agents will structure the engineering decisions.</p>
      {demo && (
        <div className="note">
          <Sparkles size={17} />
          <div>
            <strong>Demo mode uses a fixed food delivery example.</strong>
            <p>For designs based on your own idea, configure Gemini in the backend .env.</p>
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setName('Food delivery platform');
                setBrief(demoBrief);
                setConstraints(
                  'Small development team. Prefer a modular monolith and cash on delivery for the first release.',
                );
              }}
            >
              Use demonstration brief <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}
      <form onSubmit={submit}>
        <label>
          Project name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            minLength={3}
            maxLength={100}
            placeholder="e.g. Campus resource management"
          />
        </label>
        <label>
          Describe your idea
          <textarea
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            required
            minLength={30}
            maxLength={12000}
            rows={5}
            placeholder="Who is it for? What should they be able to do? What problem does it solve?"
          />
        </label>
        <label>
          Constraints & preferences <span className="muted">optional</span>
          <textarea
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
            maxLength={3000}
            rows={2}
            placeholder="Team size, budget, preferred technologies, scale…"
          />
        </label>
        <div className="review-note">
          <CheckIcon />
          Requirements pause for your review before design begins.
        </div>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
        <div className="form-footer">
          <button type="button" className="secondary" disabled={busy} onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? 'Creating…' : 'Generate blueprint'}
            <ArrowRight size={17} />
          </button>
        </div>
      </form>
    </dialog>
  );
}

function CheckIcon() {
  return <span aria-hidden="true">✓</span>;
}
