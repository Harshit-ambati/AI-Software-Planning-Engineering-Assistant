import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { BookOpen, Plus, Search } from 'lucide-react';
import { api } from '../api';
import type { Hit, Knowledge } from '../types';

export default function KnowledgePanel({ projectId, mode }: { projectId: string; mode: string }) {
  const [docs, setDocs] = useState<Knowledge[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    api<Knowledge[]>(`/projects/${projectId}/knowledge`, undefined, controller.signal)
      .then(setDocs)
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [projectId]);
  async function add(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api(`/projects/${projectId}/knowledge`, { title, content });
      setDocs(await api<Knowledge[]>(`/projects/${projectId}/knowledge`));
      setTitle('');
      setContent('');
      setShowForm(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Indexing failed.');
    } finally {
      setBusy(false);
    }
  }
  async function search(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      setHits(await api<Hit[]>(`/projects/${projectId}/knowledge/search`, { query }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed.');
    } finally {
      setBusy(false);
    }
  }
  async function reindex() {
    setBusy(true);
    setError('');
    try {
      await api(`/projects/${projectId}/knowledge/reindex`, {});
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reindex failed.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Project knowledge</h2>
          <p>Ground the next revision in your own context.</p>
        </div>
        <button className="secondary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          Add document
        </button>
      </div>
      <div className="note">
        <BookOpen size={19} />
        <div>
          <strong>
            {mode === 'semantic'
              ? 'Gemini embeddings · Qdrant retrieval'
              : 'Offline lexical retrieval · Qdrant'}
          </strong>
          <p>
            Relevant passages are selected when a revision starts. Sources stay within this project and are
            recorded with the run. Add documents before starting a new revision.
          </p>
        </div>
      </div>
      {error && (
        <p role="alert" className="error-message">
          {error}
        </p>
      )}
      {showForm && (
        <form className="knowledge-form" onSubmit={add}>
          <label>
            Document title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              minLength={3}
              maxLength={120}
              required
            />
          </label>
          <label>
            Source text
            <textarea
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              minLength={30}
              maxLength={40000}
              required
              placeholder="Paste a project brief, business rule, technical constraint or design reference…"
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? 'Indexing…' : 'Save & index document'}
          </button>
        </form>
      )}
      <form onSubmit={search} className="search-form">
        <Search size={18} />
        <input
          aria-label="Search project knowledge"
          placeholder="Find a business rule or technical decision…"
          minLength={3}
          maxLength={2000}
          required
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="secondary" disabled={busy}>
          Search
        </button>
      </form>
      {hits !== null && (
        <div className="search-results">
          <h3>Retrieved passages</h3>
          {hits.length ? (
            hits.map((hit) => (
              <article className="source-card" key={hit.citation}>
                <strong>{hit.title}</strong>
                <p>{hit.text}</p>
                <small>
                  Similarity {hit.score.toFixed(3)} · <code>{hit.citation}</code>
                </small>
              </article>
            ))
          ) : (
            <p className="muted">
              No matching indexed passages. If the embedding model changed, rebuild the index below.
            </p>
          )}
        </div>
      )}
      <div className="section-label">
        SOURCE LIBRARY <span>{docs.length} documents</span>
      </div>
      {docs.length ? (
        docs.map((doc) => (
          <details className="source-card" key={doc.id}>
            <summary>
              <BookOpen size={17} />
              <strong>{doc.title}</strong>
              <span className="muted">{new Date(doc.created_at).toLocaleDateString()}</span>
            </summary>
            <p>{doc.content}</p>
          </details>
        ))
      ) : (
        <div className="empty-inline">
          <BookOpen size={30} />
          <h3>A place for project context</h3>
          <p>
            Add business rules or reference material. Agents will retrieve relevant passages for future
            revisions.
          </p>
        </div>
      )}
      {docs.length > 0 && (
        <button className="text-button" disabled={busy} onClick={reindex}>
          Rebuild vector index from saved documents
        </button>
      )}
    </section>
  );
}
