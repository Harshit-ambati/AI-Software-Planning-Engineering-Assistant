import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Boxes,
  Check,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  Clock3,
  FileText,
  FlaskConical,
  FolderKanban,
  GitBranch,
  Layers3,
  LayoutDashboard,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Workflow,
  X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { api, download } from './api';
import ArtifactView, { ValueView } from './components/ArtifactView';
import KnowledgePanel from './components/KnowledgePanel';
import ProjectForm from './components/ProjectForm';
import RequirementsEditor from './components/RequirementsEditor';
import EvaluationPanel from './components/EvaluationPanel';
import ImpactView from './components/ImpactView';
import ReviewHistory from './components/ReviewHistory';
import type { Config, Diff, Json, Project, Report, Run, Stage, Requirements } from './types';
import { human, isActive, labels, stages } from './types';

const WorkflowGraph = lazy(() => import('./components/WorkflowGraph'));
const stageIcons: Record<Stage, LucideIcon> = {
  requirements: FileText,
  architecture: Boxes,
  database: Layers3,
  apis: GitBranch,
  implementation: FolderKanban,
  documentation: BookOpen,
  validation: ShieldCheck,
};
type View = 'overview' | 'blueprint' | 'traceability' | 'knowledge' | 'activity' | 'impact' | 'evaluation';
const tabs: { id: View; name: string; icon: LucideIcon }[] = [
  { id: 'overview', name: 'Overview', icon: LayoutDashboard },
  { id: 'blueprint', name: 'Blueprint', icon: Layers3 },
  { id: 'traceability', name: 'Traceability', icon: GitBranch },
  { id: 'impact', name: 'Impact', icon: GitBranch },
  { id: 'evaluation', name: 'Evaluation', icon: FlaskConical },
  { id: 'knowledge', name: 'Knowledge', icon: BookOpen },
  { id: 'activity', name: 'Activity', icon: Activity },
];

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [projectId, setProjectId] = useState(
    () => new URLSearchParams(location.hash.slice(1)).get('project') || '',
  );
  const [revisionId, setRevisionId] = useState(
    () => new URLSearchParams(location.hash.slice(1)).get('revision') || '',
  );
  const [project, setProject] = useState<Project | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [view, setView] = useState<View>('overview');
  const [stage, setStage] = useState<Stage>('requirements');
  const [form, setForm] = useState<'new' | 'revision' | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [reload, setReload] = useState(0);
  const [filter, setFilter] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [diff, setDiff] = useState<Diff | null>(null);
  const createdDraft = useRef<Project | null>(null);
  const [editMode, setEditMode] = useState<'edit' | 'impact' | null>(null);
  useEffect(() => {
    const params = new URLSearchParams();
    if (projectId) params.set('project', projectId);
    if (revisionId) params.set('revision', revisionId);
    history.replaceState(null, '', location.pathname + (params.size ? '#' + params.toString() : ''));
  }, [projectId, revisionId]);
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function refresh() {
      try {
        const [list, configuration] = await Promise.all([
          api<Project[]>('/projects', undefined, controller.signal),
          api<Config>('/config', undefined, controller.signal),
        ]);
        let p: Project | null = null,
          r: Run | null = null;
        if (projectId) {
          p = await api<Project>(`/projects/${projectId}`, undefined, controller.signal);
          const id = revisionId || p.runs?.[0]?.id;
          if (id) r = await api<Run>(`/runs/${id}`, undefined, controller.signal);
          if (r && r.project_id !== p.id)
            throw new Error(
              'This revision belongs to a different project. Open the project from All projects.',
            );
        }
        if (cancelled) return;
        setProjects(list);
        setConfig(configuration);
        setProject(p);
        setRun(r);
        setLoaded(true);
        setError('');
        if (isActive(r?.status)) timer = setTimeout(refresh, 1400);
      } catch (e) {
        if (cancelled) return;
        setLoaded(true);
        setError(e instanceof Error ? e.message : 'Could not connect to the workspace.');
        timer = setTimeout(refresh, 6000);
      }
    }
    void refresh();
    return () => {
      cancelled = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [projectId, revisionId, reload]);

  function selectProject(id: string) {
    setProjectId(id);
    setRevisionId('');
    setProject(null);
    setRun(null);
    setView('overview');
    setDiff(null);
  }
  function inspect(selected: Stage) {
    setStage(selected);
    setView('blueprint');
  }
  async function create(name: string, brief: string, constraints: string) {
    const p =
      form === 'revision' && project
        ? project
        : createdDraft.current || (await api<Project>('/projects', { name, brief, constraints }));
    createdDraft.current = p;
    const r = await api<Run>(`/projects/${p.id}/runs`, { brief, constraints, review_required: true });
    setProjectId(p.id);
    setRevisionId(r.id);
    setProject(p);
    setRun(r);
    setView('overview');
    setForm(null);
    setDiff(null);
    createdDraft.current = null;
    setReload((n) => n + 1);
  }
  async function action(action: 'approve' | 'reject' | 'resume') {
    if (!run) return;
    setBusy(true);
    setError('');
    try {
      const r = await api<Run>(`/runs/${run.id}/${action}`, {});
      setRun(r);
      if (action === 'reject') setForm('revision');
      setReload((n) => n + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Action failed.');
    } finally {
      setBusy(false);
    }
  }
  async function exportRun(format: string) {
    if (run)
      try {
        await download(run.id, format);
      } catch (e) {
        setError((e as Error).message);
      }
  }
  async function compareRun() {
    const index = project?.runs?.findIndex((r) => r.id === run?.id) ?? -1;
    const previous = project?.runs?.[index + 1];
    if (run && previous)
      try {
        setDiff(await api<Diff>(`/runs/${run.id}/compare/${previous.id}`));
      } catch (e) {
        setError((e as Error).message);
      }
  }
  async function startComparison(strategy: 'staged' | 'single_prompt', useMemory: boolean) {
    if (!project) return;
    const next = await api<Run>(`/projects/${project.id}/runs`, {
      brief: run?.brief || project.brief,
      constraints: run?.constraints_text || project.constraints_text,
      strategy,
      use_memory: useMemory,
      review_required: strategy === 'staged',
      parent_run_id: run?.id || null,
    });
    setRevisionId(next.id);
    setRun(next);
    setReload((n) => n + 1);
  }
  async function createFromRequirements(requirements: Requirements) {
    if (!project || !run) return;
    const next = await api<Run>(`/projects/${project.id}/runs`, {
      brief: run.brief,
      constraints: run.constraints_text,
      parent_run_id: run.id,
      requirements_seed: requirements,
      review_required: true,
      use_memory: run.use_memory ?? true,
    });
    setRevisionId(next.id);
    setRun(next);
    setView('overview');
    setDiff(null);
    setReload((n) => n + 1);
  }
  const report = run?.artifacts.validation as unknown as Report | undefined;
  const functional = (run?.artifacts.requirements as Record<string, Json> | undefined)?.functional as
    Json[] | undefined;
  const completed = stages.filter((s) => run?.artifacts[s]).length;
  const previousExists = !!project?.runs?.[project.runs.findIndex((r) => r.id === run?.id) + 1];
  const canRevise = !!project && !isActive(run?.status) && run?.status !== 'awaiting_review';
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => selectProject('')} aria-label="Forma home">
          <span className="brand-symbol">
            <Layers3 size={26} />
          </span>
          forma<span className="brand-dot">.</span>
        </button>
        <div className="workspace-switch">
          <span className="workspace-avatar">EW</span>
          <div>
            Engineering workspace<small>Personal workspace</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <button className={'side-link ' + (!projectId ? 'active' : '')} onClick={() => selectProject('')}>
          <LayoutDashboard size={18} />
          All projects<span className="nav-count">{projects.length}</span>
        </button>
        <button className="side-link" disabled={!project} onClick={() => setView('knowledge')}>
          <BookOpen size={18} />
          Project knowledge
        </button>
        <div className="nav-label projects-label">
          YOUR PROJECTS
          <button className="icon-button" aria-label="New project" onClick={() => setForm('new')}>
            <Plus size={16} />
          </button>
        </div>
        <div className="project-nav">
          {projects.slice(0, 15).map((p) => (
            <button
              className={'project-link ' + (p.id === projectId ? 'selected' : '')}
              key={p.id}
              onClick={() => selectProject(p.id)}
            >
              <span className={'project-dot ' + (p.status || '')} />
              <span>{p.name}</span>
            </button>
          ))}
          {loaded && !projects.length && <p className="sidebar-empty">Your ideas will find a home here.</p>}
        </div>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <Sparkles size={18} />
            <strong>From idea to implementation.</strong>
            <p>A clearer path through your next software project.</p>
          </div>
          <button className="side-link" onClick={() => setShowSettings(true)}>
            <Settings2 size={18} />
            Workspace settings
          </button>
          <div className="profile">
            <div className="profile-avatar">H</div>
            <div>
              Harshit’s workspace<small>Final-year engineering project</small>
            </div>
            <span className="online-dot" />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace
            <ChevronRight size={14} />
            <span>{project?.name || 'All projects'}</span>
          </div>
          <div className="topbar-right">
            <span className="local-label">
              <span className="online-dot" />
              Local workspace
            </span>
            <button
              className="icon-button"
              aria-label="Refresh workspace"
              onClick={() => setReload((n) => n + 1)}
            >
              <RefreshCw size={16} />
            </button>
            <button
              className="profile-avatar small"
              onClick={() => setShowSettings(true)}
              aria-label="Open workspace settings"
            >
              H
            </button>
          </div>
        </header>
        <main>
          {error && (
            <div role="alert" className="error-banner">
              <CircleAlert size={18} />
              <span>{error}</span>
              <button className="text-button" onClick={() => setShowSettings(true)}>
                Settings
              </button>
            </div>
          )}
          {config?.provider === 'demo' && (
            <div className="mode-banner">
              <Sparkles size={14} />
              <span>DEMONSTRATION MODE</span>Fixed food delivery blueprint · no live AI calls
              <button onClick={() => setShowSettings(true)}>
                Configure live mode <ArrowRight size={13} />
              </button>
            </div>
          )}
          {!projectId ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">YOUR ENGINEERING STUDIO</div>
                  <h1>Good software starts with a plan.</h1>
                  <p>Turn an idea into a coherent, traceable engineering blueprint.</p>
                </div>
                <button className="primary" onClick={() => setForm('new')}>
                  <Plus size={17} />
                  New project
                </button>
              </div>
              <section className="hero">
                <div className="hero-copy">
                  <span className="hero-tag">
                    <span className="online-dot" />A STRUCTURED APPROACH TO BUILDING
                  </span>
                  <h2>
                    Less guesswork.
                    <br />
                    More engineering.
                  </h2>
                  <p>
                    Specialized agents work through your requirements, architecture and APIs—with your review
                    and validation at every important step.
                  </p>
                  <button className="hero-button" onClick={() => setForm('new')}>
                    Start with an idea <ArrowRight size={18} />
                  </button>
                  <div className="hero-footnote">
                    <ShieldCheck size={14} />
                    Traceable decisions. Inspectable outputs.
                  </div>
                </div>
                <div className="hero-visual" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="visual-line" />
                  <div className="visual-card input-card">
                    <span className="visual-icon">
                      <FileText size={18} />
                    </span>
                    <div>
                      <small>THE STARTING POINT</small>
                      <strong>Your software idea</strong>
                    </div>
                    <span className="visual-pill">01</span>
                  </div>
                  <div className="visual-agent">
                    <Boxes size={24} />
                    <span>Specialized agents</span>
                    <div className="agent-dots">
                      <i />
                      <i />
                      <i />
                      <i />
                      <i />
                    </div>
                  </div>
                  <div className="visual-card output-card">
                    <span className="visual-icon">
                      <ShieldCheck size={19} />
                    </span>
                    <div>
                      <small>THE ENGINEERING BLUEPRINT</small>
                      <strong>Designed. Connected. Checked.</strong>
                    </div>
                    <Check size={18} />
                  </div>
                  <span className="floating-label label-one">Requirements</span>
                  <span className="floating-label label-two">Architecture</span>
                  <span className="floating-label label-three">Validation</span>
                </div>
              </section>
              <div className="home-stats">
                <Metric
                  icon={FolderKanban}
                  label="Total projects"
                  value={projects.length}
                  hint="Ideas in your workspace"
                />
                <Metric
                  icon={ShieldCheck}
                  label="Checks passed"
                  value={projects.filter((p) => p.status === 'passed').length}
                  hint="Latest revision per project"
                />
                <Metric icon={Workflow} label="Engineering stages" value="07" hint="One connected workflow" />
              </div>
              <section className="projects-section">
                <div className="section-heading">
                  <div>
                    <h2>
                      Your projects <span className="count-badge">{projects.length}</span>
                    </h2>
                    <p>Pick up where you left off, or explore a new idea.</p>
                  </div>
                  <div className="filter">
                    <Search size={16} />
                    <input
                      aria-label="Filter projects"
                      placeholder="Find a project…"
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                    />
                  </div>
                </div>
                {!loaded ? (
                  <div className="empty-inline">
                    <span className="spinner" />
                    Connecting to workspace…
                  </div>
                ) : projects.length ? (
                  <div className="project-grid">
                    {projects
                      .filter((p) => p.name.toLowerCase().includes(filter.toLowerCase()))
                      .map((p) => (
                        <button key={p.id} className="project-card" onClick={() => selectProject(p.id)}>
                          <div className="project-card-top">
                            <span className="project-icon">
                              <FolderKanban size={22} />
                            </span>
                            <Status value={p.status || 'draft'} />
                          </div>
                          <h3>{p.name}</h3>
                          <p>{p.brief}</p>
                          <div className="project-card-bottom">
                            <span>
                              {p.run_count} revisions · {new Date(p.created_at).toLocaleDateString()}
                            </span>
                            <ArrowRight size={17} />
                          </div>
                        </button>
                      ))}
                    {filter && !projects.some((p) => p.name.toLowerCase().includes(filter.toLowerCase())) && (
                      <p className="muted">No matching projects.</p>
                    )}
                  </div>
                ) : (
                  <div className="empty-projects">
                    <div className="empty-project-icon">
                      <FolderKanban size={29} />
                    </div>
                    <h3>Every great build starts here.</h3>
                    <p>Describe your idea and let the engineering workflow take shape.</p>
                    <button className="secondary" onClick={() => setForm('new')}>
                      <Plus size={16} />
                      Create your first project
                    </button>
                  </div>
                )}
              </section>
              <div className="home-footer">
                <span>BUILT FOR THOUGHTFUL ENGINEERING</span>
                <div>
                  <GitBranch size={14} />
                  Requirements → design → verification
                </div>
              </div>
            </>
          ) : project ? (
            <>
              <div className="page-heading project-title">
                <div>
                  <div className="eyebrow">
                    PROJECT WORKSPACE <span>/</span>{' '}
                    {run ? `REVISION ${String(run.version).padStart(2, '0')}` : 'DRAFT'}
                  </div>
                  <h1>{project.name}</h1>
                  <p>
                    {run
                      ? `${run.provider === 'demo' ? 'Demonstration fixture' : run.model} · ${run.strategy === 'single_prompt' ? 'Single-prompt baseline' : 'Staged workflow'} · Created ${new Date(run.created_at).toLocaleString()}`
                      : 'Your project is ready for its first blueprint.'}
                  </p>
                </div>
                <div className="heading-actions">
                  <button className="secondary" disabled={!canRevise} onClick={() => setForm('revision')}>
                    <Plus size={16} />
                    New revision
                  </button>
                  {run && (
                    <details className="export-menu">
                      <summary className="primary">
                        <ArrowDownToLine size={16} />
                        Export
                        <ChevronDown size={14} />
                      </summary>
                      <div>
                        {['markdown', 'json', 'openapi'].map((format) => (
                          <button key={format} onClick={() => void exportRun(format)}>
                            {format === 'openapi' ? 'OpenAPI 3.1' : human(format)}
                          </button>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>
              <div className="workspace-toolbar">
                <div className="tabs">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={view === tab.id ? 'active' : ''}
                      onClick={() => setView(tab.id)}
                    >
                      <tab.icon size={16} />
                      {tab.name}
                    </button>
                  ))}
                </div>
                <div className="revision-selector">
                  <GitBranch size={14} />
                  <select
                    aria-label="Select revision"
                    value={revisionId || run?.id || ''}
                    onChange={(e) => {
                      setRevisionId(e.target.value);
                      setDiff(null);
                    }}
                  >
                    {project.runs?.map((r) => (
                      <option key={r.id} value={r.id}>
                        Revision {r.version} · {human(r.id === run?.id ? run.status : r.status)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {run?.status === 'awaiting_review' && (
                <div className="review-banner">
                  <span className="review-icon">
                    <ShieldCheck size={24} />
                  </span>
                  <div>
                    <strong>Your requirements are ready for review.</strong>
                    <p>Inspect the scope before agents make downstream design decisions.</p>
                  </div>
                  <button className="text-button" onClick={() => inspect('requirements')}>
                    Inspect
                  </button>
                  <button className="secondary" disabled={busy} onClick={() => setEditMode('edit')}>
                    Edit requirements
                  </button>
                  <button className="secondary" disabled={busy} onClick={() => void action('reject')}>
                    Revise scope
                  </button>
                  <button className="primary" disabled={busy} onClick={() => void action('approve')}>
                    Approve & continue
                    <ArrowRight size={15} />
                  </button>
                </div>
              )}
              {run && ['failed', 'interrupted'].includes(run.status) && (
                <div className="error-banner">
                  <CircleAlert size={20} />
                  <div>
                    <strong>{human(run.status)}</strong>
                    <p>
                      {run.error ||
                        'The server stopped during this revision. Resume from the last saved checkpoint.'}
                    </p>
                  </div>
                  <button className="secondary" disabled={busy} onClick={() => void action('resume')}>
                    Resume revision
                  </button>
                </div>
              )}
              {view === 'overview' && (
                <>
                  <div className="workspace-stats">
                    <Metric
                      icon={FileText}
                      label="Requirements"
                      value={functional?.length || 0}
                      hint="Functional requirements identified"
                    />
                    <Metric
                      icon={Workflow}
                      label="Artifacts complete"
                      value={`${completed} / 7`}
                      hint="Saved across the workflow"
                    />
                    <Metric
                      icon={ShieldCheck}
                      label="Linked coverage"
                      value={report ? `${report.coverage_percent}%` : '—'}
                      hint="Available after validation"
                    />
                    <Metric
                      icon={Clock3}
                      label="Revision status"
                      value={<Status value={run?.status || 'draft'} />}
                      hint="Persisted workflow state"
                    />
                  </div>
                  <section className="panel workflow-panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">THE ENGINEERING PROCESS</span>
                        <h2>One idea. A connected workflow.</h2>
                        <p>Select a stage to inspect its artifact.</p>
                      </div>
                      <span className="tag">
                        <span className={isActive(run?.status) ? 'pulse-dot' : 'online-dot'} />
                        {isActive(run?.status) ? 'Agents working' : `${completed} of 7 completed`}
                      </span>
                    </div>
                    <Suspense fallback={<div className="graph loading">Loading workflow…</div>}>
                      <WorkflowGraph run={run} onSelect={inspect} />
                    </Suspense>
                    <div className="workflow-caption">
                      <ShieldCheck size={15} />
                      {run?.strategy === 'single_prompt'
                        ? 'Baseline artifacts are generated together in one response; the experiment skips human review.'
                        : 'Human review follows requirement analysis. Every completed artifact is saved.'}
                    </div>
                  </section>
                  <div className="overview-columns">
                    <section className="panel brief-panel">
                      <div className="panel-heading">
                        <h2>The project brief</h2>
                        <FileText size={19} />
                      </div>
                      <p>{run?.brief || project.brief}</p>
                      {(run?.constraints_text || project.constraints_text) && (
                        <>
                          <h4>Constraints & preferences</h4>
                          <p className="muted">{run?.constraints_text || project.constraints_text}</p>
                        </>
                      )}
                      <div className="brief-footer">
                        <span className="tag">
                          {run?.provider === 'demo' ? 'Fixed demo example' : 'User-defined scope'}
                        </span>
                        {canRevise && (
                          <button className="text-button" onClick={() => setForm('revision')}>
                            Refine in a new revision <ArrowRight size={14} />
                          </button>
                        )}
                      </div>
                    </section>
                    <section className="panel next-panel">
                      <span className="eyebrow">NEXT IN YOUR WORKSPACE</span>
                      <h2>
                        {run?.status === 'awaiting_review'
                          ? 'A moment for your judgment.'
                          : report
                            ? 'Ready for a closer look.'
                            : 'The blueprint is taking shape.'}
                      </h2>
                      <p>
                        {report
                          ? 'Inspect requirement coverage and review findings before starting implementation.'
                          : 'Your review of the requirements sets the direction for every design decision that follows.'}
                      </p>
                      <button
                        className="text-button"
                        onClick={() => (report ? setView('traceability') : inspect('requirements'))}
                      >
                        {report ? 'Explore traceability' : 'Review requirements'}
                        <ArrowRight size={16} />
                      </button>
                    </section>
                  </div>
                </>
              )}
              {view === 'blueprint' && (
                <div className="blueprint-layout">
                  <aside className="artifact-nav">
                    <div className="section-label">ARTIFACTS</div>
                    {stages.map((s) => {
                      const Icon = stageIcons[s];
                      return (
                        <button className={stage === s ? 'active' : ''} key={s} onClick={() => setStage(s)}>
                          <Icon size={17} />
                          {labels[s]}
                          {run?.artifacts[s] ? (
                            <Check size={14} className="green" />
                          ) : (
                            <span className="pending-dot" />
                          )}
                        </button>
                      );
                    })}
                    <div className="artifact-nav-note">
                      <GitBranch size={16} />
                      <p>Each artifact carries the IDs that connect your design.</p>
                    </div>
                  </aside>
                  <section className="panel artifact-content">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">
                          ENGINEERING ARTIFACT {String(stages.indexOf(stage) + 1).padStart(2, '0')}
                        </span>
                        <h2>{labels[stage]}</h2>
                      </div>
                      {run?.artifacts[stage] && (
                        <span className="tag">
                          <Check size={13} />
                          Saved
                        </span>
                      )}
                    </div>
                    {run?.artifacts[stage] ? (
                      <ArtifactView stage={stage} value={run.artifacts[stage]!} />
                    ) : (
                      <div className="empty-inline">
                        <Clock3 size={30} />
                        <h3>This stage is waiting.</h3>
                        <p>
                          {run?.status === 'awaiting_review'
                            ? 'Approve requirements to continue the workflow.'
                            : 'The artifact appears here after this agent finishes.'}
                        </p>
                      </div>
                    )}
                  </section>
                </div>
              )}
              {view === 'traceability' && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Requirement traceability</h2>
                      <p>Follow each requirement through the engineering blueprint.</p>
                    </div>
                    {previousExists && (
                      <button className="secondary" onClick={() => void compareRun()}>
                        <GitBranch size={16} />
                        Compare previous revision
                      </button>
                    )}
                  </div>
                  {report ? (
                    <>
                      <div className="table-scroll">
                        <table className="trace-table">
                          <thead>
                            <tr>
                              <th>Requirement</th>
                              <th>Components</th>
                              <th>Entities</th>
                              <th>Endpoints</th>
                              <th>Tasks</th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.coverage.map((row) => (
                              <tr key={row.requirement_id}>
                                <td>
                                  <code>{row.requirement_id}</code>
                                  <strong>{row.title}</strong>
                                </td>
                                {(['architecture', 'database', 'apis', 'implementation'] as const).map(
                                  (key) => (
                                    <td key={key}>
                                      {row[key].length ? (
                                        row[key].map((id) => (
                                          <span className="trace-id" key={id}>
                                            {id}
                                          </span>
                                        ))
                                      ) : (
                                        <span className="muted">—</span>
                                      )}
                                    </td>
                                  ),
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="note">
                        Links show declared coverage. Inspect endpoint behavior and acceptance criteria to
                        evaluate actual completeness.
                      </div>
                    </>
                  ) : (
                    <div className="empty-inline">
                      <GitBranch size={30} />
                      <h3>Traceability appears after validation.</h3>
                      <p>
                        The validation stage connects requirements to components, entities, endpoints and
                        tasks.
                      </p>
                    </div>
                  )}
                  {diff && (
                    <div className="revision-diff">
                      <h3>
                        Revision {diff.before_version} → {diff.after_version}
                      </h3>
                      <p>
                        {diff.brief_changed
                          ? 'The project brief changed.'
                          : 'The project brief is unchanged.'}{' '}
                        {diff.changes.length} artifact fields changed.
                      </p>
                      {diff.impact && <ImpactView impact={diff.impact} />}
                      {diff.changes.map((change) => (
                        <details key={change.path}>
                          <summary>
                            <code>{change.path}</code>
                          </summary>
                          <div className="diff-columns">
                            <div>
                              <small>BEFORE</small>
                              <ValueView value={change.before} />
                            </div>
                            <div>
                              <small>AFTER</small>
                              <ValueView value={change.after} />
                            </div>
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                </section>
              )}
              {view === 'impact' && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">FOLLOW THE CONSEQUENCES OF A CHANGE</span>
                      <h2>Requirement change impact</h2>
                      <p>Preview affected design records and task dependencies before creating a revision.</p>
                    </div>
                  </div>
                  <div className="note">
                    Select a completed revision as the baseline. Change a requirement, analyze its linked
                    components, entities, endpoints and dependent tasks, then create a separate revised
                    blueprint. Scope and NFR changes conservatively flag every design record.
                  </div>
                  <button
                    className="primary"
                    disabled={!run?.artifacts.requirements || !canRevise}
                    onClick={() => setEditMode('impact')}
                  >
                    <GitBranch size={16} />
                    Propose a requirement change
                  </button>
                  {previousExists && (
                    <button className="secondary impact-compare" onClick={() => void compareRun()}>
                      Analyze previous → current revision
                    </button>
                  )}
                  {diff?.impact && <ImpactView impact={diff.impact} />}
                </section>
              )}
              {view === 'evaluation' && (
                <EvaluationPanel
                  project={project}
                  run={run}
                  onStart={startComparison}
                  onSelect={(id) => setRevisionId(id)}
                />
              )}
              {view === 'knowledge' && (
                <KnowledgePanel
                  key={project.id}
                  projectId={project.id}
                  mode={config?.memory || 'lexical demo'}
                />
              )}
              {view === 'activity' && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Execution history</h2>
                      <p>Persisted events, model usage and source provenance for this revision.</p>
                    </div>
                    <Status value={run?.status || 'draft'} />
                  </div>
                  <div className="activity-list">
                    {run?.events.map((event) => (
                      <div className="activity-item" key={event.id}>
                        <span className={'event-dot ' + event.status} />
                        <time>{new Date(event.created_at).toLocaleTimeString()}</time>
                        <div>
                          <strong>{human(event.stage)}</strong>
                          <p>{human(event.status)}</p>
                          {Object.keys(event.detail).length > 0 && (
                            <details>
                              <summary>Execution details</summary>
                              <ValueView value={event.detail} />
                            </details>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {run && <ReviewHistory key={run.id} runId={run.id} />}
                  {run?.artifacts.sources && (
                    <details className="source-card">
                      <summary>
                        <BookOpen size={16} />
                        Retrieved source passages
                      </summary>
                      <ValueView value={run.artifacts.sources} />
                    </details>
                  )}
                </section>
              )}
            </>
          ) : (
            <div className="empty-inline">
              <span className="spinner" />
              Loading project workspace…
            </div>
          )}
        </main>
        <footer className="app-footer">
          <span>Forma / Engineering with intent</span>
          <span>Blueprint workspace · v2.1</span>
        </footer>
      </div>
      {form && (
        <ProjectForm
          key={form + (run?.id || '')}
          project={
            form === 'revision' && project
              ? {
                  ...project,
                  brief: run?.brief || project.brief,
                  constraints_text: run?.constraints_text || project.constraints_text,
                }
              : undefined
          }
          demo={config?.provider === 'demo'}
          onClose={() => {
            createdDraft.current = null;
            setForm(null);
          }}
          onSubmit={create}
        />
      )}
      {editMode && run?.artifacts.requirements && (
        <RequirementsEditor
          key={run.id + editMode}
          run={run}
          mode={editMode}
          onClose={() => setEditMode(null)}
          onSaved={(next) => {
            setRun(next);
            setReload((n) => n + 1);
          }}
          onCreate={createFromRequirements}
        />
      )}
      {showSettings && (
        <SettingsDialog
          config={config}
          onClose={() => setShowSettings(false)}
          onSave={() => {
            setShowSettings(false);
            setReload((n) => n + 1);
          }}
        />
      )}
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: LucideIcon;
  label: string;
  value: React.ReactNode;
  hint: string;
}) {
  return (
    <div className="metric">
      <div className="metric-label">
        <span>{label}</span>
        <Icon size={18} />
      </div>
      <div className="metric-value">{value}</div>
      <small>{hint}</small>
    </div>
  );
}
function Status({ value }: { value: string }) {
  return (
    <span className={'status ' + value}>
      <span />
      {human(value)}
    </span>
  );
}
function SettingsDialog({
  config,
  onClose,
  onSave,
}: {
  config: Config | null;
  onClose: () => void;
  onSave: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [token, setToken] = useState(sessionStorage.getItem('forma-access-token') || '');
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog ref={dialog} className="settings-dialog" onCancel={onClose}>
      <div className="modal-heading">
        <h2>Workspace settings</h2>
        <button className="icon-button" aria-label="Close settings" onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      <div className="note">
        <Settings2 size={18} />
        <div>
          <strong>{config ? `${human(config.provider)} · ${config.model}` : 'Backend connection'}</strong>
          <p>
            For live generation, set AI_PROVIDER=gemini and GEMINI_API_KEY in the root .env, then restart the
            backend. Choose a model available to your account with GEMINI_MODEL.
          </p>
          <p>API keys stay on the server. This form only accepts the optional workspace access token.</p>
        </div>
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          sessionStorage.setItem('forma-access-token', token.trim());
          onSave();
        }}
      >
        <label>
          Workspace access token
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Only needed if APP_ACCESS_TOKEN is configured"
          />
        </label>
        <p className="muted">Stored for this browser session. This is a single-user workspace.</p>
        <div className="form-footer">
          <button type="button" className="secondary" onClick={onClose}>
            Close
          </button>
          <button className="primary">Save connection</button>
        </div>
      </form>
    </dialog>
  );
}
