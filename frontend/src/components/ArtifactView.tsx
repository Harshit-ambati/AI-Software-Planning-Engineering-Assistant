import { Check, ChevronDown, CircleAlert, FileCode2 } from 'lucide-react';
import type { Json, Report, Stage } from '../types';
import { human } from '../types';

function primitive(value: Json): string {
  return value === null ? '—' : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);
}

export function ValueView({ value }: { value: Json }) {
  if (Array.isArray(value))
    return value.length ? (
      <ul className="value-list">
        {value.map((item, i) => (
          <li key={i}>
            <ValueView value={item} />
          </li>
        ))}
      </ul>
    ) : (
      <span className="muted">None specified</span>
    );
  if (value !== null && typeof value === 'object')
    return (
      <dl className="value-grid">
        {Object.entries(value).map(([key, val]) => (
          <div key={key}>
            <dt>{human(key)}</dt>
            <dd>
              <ValueView value={val} />
            </dd>
          </div>
        ))}
      </dl>
    );
  return <span className="plain-value">{primitive(value)}</span>;
}

export function ValidationView({ report }: { report: Report }) {
  return (
    <>
      <div className={'report-summary ' + (report.findings.length ? 'attention' : '')}>
        {report.findings.length ? <CircleAlert size={25} /> : <Check size={25} />}
        <div>
          <h3>
            {report.findings.length
              ? 'Review findings before implementation'
              : 'All implemented checks passed'}
          </h3>
          <p>
            {report.coverage_percent}% linked requirement coverage · {report.findings.length} findings
          </p>
        </div>
      </div>
      <section className="artifact-section">
        <h3>Business-behavior review</h3>
        <p className="muted">
          Automated semantic coverage:{' '}
          {report.semantic_coverage_percent == null ? 'Not assessed' : `${report.semantic_coverage_percent}%`}
          . This is a reviewer judgment, not proof of correctness.
        </p>
        {report.semantic_assessments?.map((item) => (
          <div className="finding" key={item.requirement_id}>
            <span className="tag">{item.status}</span>
            <div>
              <strong>
                {item.requirement_id} · {item.endpoint_ids.join(', ') || 'No endpoint evidence'}
              </strong>
              <p>{item.explanation}</p>
            </div>
          </div>
        ))}
      </section>
      {!!report.source_assessments?.length && (
        <section className="artifact-section">
          <h3>Retrieved-rule conformance</h3>
          {report.source_assessments.map((item) => (
            <div className="finding" key={item.citation}>
              <span className="tag">{item.status}</span>
              <div>
                <code>{item.citation}</code>
                <p>{item.explanation}</p>
                <small>{[...item.requirement_ids, ...item.endpoint_ids].join(', ')}</small>
              </div>
            </div>
          ))}
        </section>
      )}
      {report.findings.map((finding, i) => (
        <div className="finding" key={i}>
          <span className={'status ' + finding.severity}>{finding.severity}</span>
          <div>
            <strong>
              {finding.rule} · {finding.reference}
            </strong>
            <p>{finding.message}</p>
            <small>{human(finding.artifact)}</small>
          </div>
        </div>
      ))}
      <div className="note">
        <strong>What this report can verify</strong>
        {report.limitations.map((text, i) => (
          <p key={i}>{text}</p>
        ))}
      </div>
    </>
  );
}

export default function ArtifactView({ stage, value }: { stage: Stage; value: Json }) {
  if (stage === 'validation') return <ValidationView report={value as unknown as Report} />;
  const object = value as Record<string, Json>;
  if (stage === 'apis')
    return (
      <>
        <div className="note">
          <strong>Authentication</strong>
          <p>{String(object.authentication)}</p>
        </div>
        {(object.endpoints as Record<string, Json>[]).map((endpoint) => (
          <details className="endpoint" key={String(endpoint.id)}>
            <summary>
              <span className={'method ' + endpoint.method}>{String(endpoint.method)}</span>
              <code>{String(endpoint.path)}</code>
              <span className="endpoint-summary">{String(endpoint.summary)}</span>
              <ChevronDown size={16} />
            </summary>
            <div className="endpoint-body">
              <ValueView value={endpoint} />
            </div>
          </details>
        ))}
      </>
    );
  if (stage === 'requirements')
    return (
      <>
        <p className="artifact-intro">{String(object.summary)}</p>
        <div className="tag-row">
          {(object.actors as string[]).map((actor) => (
            <span className="tag" key={actor}>
              {actor}
            </span>
          ))}
        </div>
        {(object.functional as Record<string, Json>[]).map((req) => (
          <article className="requirement-card" key={String(req.id)}>
            <div className="card-top">
              <code>{String(req.id)}</code>
              <span className="priority">{String(req.priority)} have</span>
            </div>
            <h3>{String(req.title)}</h3>
            <p>{String(req.description)}</p>
            <ul className="criteria">
              {(req.acceptance_criteria as string[]).map((text, i) => (
                <li key={i}>
                  <Check size={14} />
                  {text}
                </li>
              ))}
            </ul>
          </article>
        ))}
        {Object.entries(object)
          .filter(([key]) => !['summary', 'actors', 'functional'].includes(key))
          .map(([key, val]) => (
            <section className="artifact-section" key={key}>
              <h3>{human(key)}</h3>
              <ValueView value={val} />
            </section>
          ))}
      </>
    );
  if (stage === 'database')
    return (
      <>
        <div className="note">
          <FileCode2 size={18} />
          <strong>{String(object.engine)} schema proposal</strong>
        </div>
        {(object.entities as Record<string, Json>[]).map((entity) => (
          <section className="entity" key={String(entity.id)}>
            <div className="entity-heading">
              <h3>{String(entity.name)}</h3>
              <code>{String(entity.id)}</code>
            </div>
            <p>{String(entity.description)}</p>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {(entity.fields as Record<string, Json>[]).map((field) => (
                    <tr key={String(field.name)}>
                      <td>
                        <code>{String(field.name)}</code>
                      </td>
                      <td>{String(field.type)}</td>
                      <td>{field.required ? 'Yes' : 'No'}</td>
                      <td>{String(field.description)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="entity-footer">
              {(entity.indexes as string[]).map((index) => (
                <code key={index}>{index}</code>
              ))}
              <span className="muted">Linked: {(entity.requirement_ids as string[]).join(', ')}</span>
            </div>
          </section>
        ))}
        <section className="artifact-section">
          <h3>Relationships</h3>
          <ValueView value={object.relationships} />
        </section>
      </>
    );
  return (
    <>
      {Object.entries(object).map(([key, val]) => (
        <section className="artifact-section" key={key}>
          <h3>{human(key)}</h3>
          <ValueView value={val} />
        </section>
      ))}
    </>
  );
}
