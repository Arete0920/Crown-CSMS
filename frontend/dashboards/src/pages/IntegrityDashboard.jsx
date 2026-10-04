import { useEffect, useMemo, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

function sessionHeaders({ includeSchool = false } = {}) {
  const headers = { Accept: 'application/json' };
  try {
    const token = sessionStorage.getItem('crown.jwt.access') || '';
    const schoolId = sessionStorage.getItem('crown.school.id') || '';
    if (token) headers.Authorization = `Bearer ${token}`;
    if (includeSchool && schoolId) headers['X-School-Id'] = schoolId;
  } catch {
    // The request will fail closed if required session context is unavailable.
  }
  return headers;
}

async function fetchJson(path, { includeSchool = false } = {}) {
  try {
    const res = await globalThis.fetch(`${apiBase()}${path}`, {
      headers: sessionHeaders({ includeSchool }),
    });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch {
    return { ok: false, data: null };
  }
}

function Pill({ color = 'gray', children }) {
  const map = {
    red: { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)' },
    yellow: { bg: 'var(--crown-warn-bg)', fg: 'var(--crown-warn)' },
    green: { bg: 'var(--crown-ok-bg)', fg: 'var(--crown-ok)' },
    blue: { bg: 'var(--crown-surface-2)', fg: 'var(--crown-brand)' },
    gray: { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)' },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 9px',
      fontSize: 11,
      fontWeight: 700,
      borderRadius: 999,
      background: v.bg,
      color: v.fg,
    }}>
      {children}
    </span>
  );
}

function severityColor(severity) {
  if (severity === 'critical') return 'red';
  if (severity === 'high' || severity === 'medium') return 'yellow';
  if (severity === 'low') return 'blue';
  return 'gray';
}

function CheckRow({ label, ok = true }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '6px 0',
      borderBottom: '1px solid var(--crown-border)',
    }}>
      <span style={{ fontSize: 16, color: ok ? 'var(--crown-ok)' : 'var(--crown-danger)' }}>
        {ok ? '[ok]' : '[x]'}
      </span>
      <span style={{
        fontSize: 13,
        fontFamily: 'var(--crown-font-mono)',
        color: 'var(--crown-ink)',
      }}>
        {label}
      </span>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  return (
    <button
      onClick={handleCopy}
      title="Copy full SHA"
      style={{
        marginLeft: 6,
        padding: '1px 7px',
        fontSize: 11,
        fontFamily: 'var(--crown-font-mono)',
        color: copied ? 'var(--crown-ok)' : 'var(--crown-muted)',
        background: copied ? 'var(--crown-ok-bg)' : 'var(--crown-surface-2)',
        border: '1px solid var(--crown-border)',
        borderRadius: 6,
        cursor: 'pointer',
        lineHeight: '18px',
      }}
    >
      {copied ? 'copied!' : 'copy'}
    </button>
  );
}

function ShaLink({ sha, url }) {
  const short = sha && sha !== 'local-dev' ? sha.slice(0, 7) : sha;
  const isReal = sha && sha !== 'local-dev';

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center' }}>
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          style={{
            fontFamily: 'var(--crown-font-mono)',
            fontSize: 13,
            color: 'var(--crown-brand)',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          {short}
        </a>
      ) : (
        <code style={{ fontSize: 13, color: 'var(--crown-muted)' }}>{short}</code>
      )}
      {isReal && <CopyButton text={sha} />}
    </span>
  );
}

function CopyProofButton({ data }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    const proof = JSON.stringify({
      sha: data.build_sha,
      env: data.env,
      tag: data.prod_deploy_tag || null,
      checks_count: data.required_checks?.length ?? 0,
      timestamp: data.timestamp,
    }, null, 2);

    navigator.clipboard.writeText(proof).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  return (
    <button
      onClick={handleCopy}
      title="Copy integrity proof as JSON"
      style={{
        marginLeft: 8,
        padding: '2px 10px',
        fontSize: 11,
        fontFamily: 'var(--crown-font-mono)',
        color: copied ? 'var(--crown-ok)' : 'var(--crown-brand)',
        background: copied ? 'var(--crown-ok-bg)' : 'var(--crown-surface-2)',
        border: '1px solid var(--crown-border)',
        borderRadius: 6,
        cursor: 'pointer',
        lineHeight: '18px',
      }}
    >
      {copied ? 'copied!' : 'copy proof'}
    </button>
  );
}

function DataQualityRow({ check }) {
  const clear = check.status === 'pass';
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'minmax(190px, 1.25fr) 90px minmax(220px, 2fr)',
      gap: 14,
      alignItems: 'start',
      padding: '12px 0',
      borderBottom: '1px solid var(--crown-border)',
    }}>
      <div>
        <div style={{ fontWeight: 700, color: 'var(--crown-ink)', fontSize: 13 }}>
          {check.label}
        </div>
        <div style={{ marginTop: 4, color: 'var(--crown-muted)', fontSize: 12, lineHeight: 1.45 }}>
          {check.description}
        </div>
      </div>
      <div>
        <Pill color={clear ? 'green' : severityColor(check.severity)}>
          {clear ? 'CLEAR' : `${check.count} ${check.severity.toUpperCase()}`}
        </Pill>
      </div>
      <div style={{ color: 'var(--crown-muted)', fontSize: 12, lineHeight: 1.45 }}>
        {clear ? 'No review action required.' : check.action}
      </div>
    </div>
  );
}

export default function IntegrityDashboard() {
  const [systemState, setSystemState] = useState({
    loading: true,
    error: false,
    data: null,
  });
  const [qualityState, setQualityState] = useState({
    loading: true,
    error: false,
    data: null,
  });

  useEffect(() => {
    fetchJson('/api/integrity/').then(({ ok, data }) => {
      setSystemState({
        loading: false,
        error: !ok || !data?.ok,
        data: ok ? data : null,
      });
    });

    fetchJson('/api/v1/integrity/data-quality/', { includeSchool: true }).then(({ ok, data }) => {
      setQualityState({
        loading: false,
        error: !ok || !data?.summary,
        data: ok ? data : null,
      });
    });
  }, []);

  const kpis = useMemo(() => {
    const summary = qualityState.data?.summary;
    const checks = qualityState.data?.checks || [];
    const clearCount = checks.filter((check) => check.status === 'pass').length;

    if (!summary) {
      const value = qualityState.loading ? '...' : '—';
      return [
        {
          label: 'Open Findings',
          value,
          definition: 'Aggregate school-data conditions that require human review.',
          dataSource: 'School Data Quality',
        },
        {
          label: 'Critical',
          value,
          definition: 'Cross-tenant or similarly severe integrity conditions requiring immediate review.',
          dataSource: 'School Data Quality',
        },
        {
          label: 'High Priority',
          value,
          definition: 'High-severity school-data configuration or lifecycle conditions.',
          dataSource: 'School Data Quality',
        },
        {
          label: 'Checks Clear',
          value,
          definition: 'Data-quality checks with no current findings.',
          dataSource: 'School Data Quality',
        },
      ];
    }

    return [
      {
        label: 'Open Findings',
        value: String(summary.findings_count ?? 0),
        definition: 'Aggregate school-data conditions that require human review.',
        dataSource: 'School Data Quality API',
      },
      {
        label: 'Critical',
        value: String(summary.critical ?? 0),
        definition: 'Cross-tenant or similarly severe integrity conditions requiring immediate review.',
        dataSource: 'School Data Quality API',
      },
      {
        label: 'High Priority',
        value: String(summary.high ?? 0),
        definition: 'High-severity school-data configuration or lifecycle conditions.',
        dataSource: 'School Data Quality API',
      },
      {
        label: 'Checks Clear',
        value: String(clearCount),
        definition: 'Data-quality checks with no current findings.',
        dataSource: 'School Data Quality API',
      },
    ];
  }, [qualityState]);

  const { loading, error, data } = systemState;
  const envColor = data?.env === 'prod' ? 'green' : data?.env === 'dev' ? 'yellow' : 'gray';
  const timestamp = data?.timestamp
    ? new Date(data.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : '';
  const qualityTimestamp = qualityState.data?.generated_at
    ? new Date(qualityState.data.generated_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : '';

  return (
    <CrownLayout
      title="Crown Integrity"
      subtitle="School data quality and system verification"
    >
      <KpiStrip cards={kpis} />
      <CrownGrid>
        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '4px 0 12px' }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--crown-ink)' }}>
              School Data Quality
            </span>
            {!qualityState.loading && !qualityState.error && (
              <Pill color={qualityState.data?.summary?.findings_count ? 'yellow' : 'green'}>
                {qualityState.data?.summary?.findings_count ? 'REVIEW' : 'CLEAR'}
              </Pill>
            )}
            {qualityState.error && <Pill color="yellow">UNAVAILABLE</Pill>}
            {qualityState.loading && <Pill color="gray">Loading</Pill>}
            {qualityTimestamp && (
              <span style={{ fontSize: 12, color: 'var(--crown-muted)' }}>
                Checked {qualityTimestamp}
              </span>
            )}
          </div>
        </Col>

        <Col span={12}>
          <CrownCard
            title="School Data Quality"
            right={qualityState.data ? (
              <Pill color="blue">READ ONLY</Pill>
            ) : null}
          >
            {qualityState.loading && (
              <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>
                Checking tenant-scoped school data.
              </p>
            )}
            {qualityState.error && (
              <div>
                <p style={{ color: 'var(--crown-danger)', fontSize: 13, marginBottom: 4 }}>
                  School data quality is unavailable.
                </p>
                <p style={{ color: 'var(--crown-muted)', fontSize: 12 }}>
                  No fallback or sample findings are displayed.
                </p>
              </div>
            )}
            {qualityState.data?.checks?.map((check) => (
              <DataQualityRow key={check.id} check={check} />
            ))}
            {qualityState.data && (
              <p style={{
                margin: '12px 0 0',
                fontSize: 11,
                color: 'var(--crown-muted)',
                lineHeight: 1.5,
              }}>
                Findings are aggregate and tenant-scoped. Crown does not automatically merge,
                relink, or rewrite identity records from this screen.
              </p>
            )}
          </CrownCard>
        </Col>

        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 0 2px' }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--crown-ink)' }}>
              System Verification
            </span>
            {!loading && !error && <Pill color="green">LIVE</Pill>}
            {error && <Pill color="yellow">UNAVAILABLE</Pill>}
            {loading && <Pill color="gray">Loading</Pill>}
            {!loading && !error && data && <CopyProofButton data={data} />}
          </div>
        </Col>

        <Col span={6}>
          <CrownCard title="Deployment">
            {loading && <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>Fetching</p>}
            {error && (
              <p style={{ color: 'var(--crown-danger)', fontSize: 13 }}>
                Could not reach /api/integrity/
              </p>
            )}
            {data && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)', width: 120 }}>
                      Build SHA
                    </td>
                    <td><ShaLink sha={data.build_sha} url={data.github_commit_url} /></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Environment</td>
                    <td><Pill color={envColor}>{data.env}</Pill></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Version</td>
                    <td style={{ fontFamily: 'var(--crown-font-mono)', color: 'var(--crown-ink)' }}>
                      {data.version}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Checked at</td>
                    <td style={{ color: 'var(--crown-ink)' }}>{timestamp}</td>
                  </tr>
                  {data.env === 'prod' && (
                    <tr>
                      <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Deploy tag</td>
                      <td>
                        {data.github_tag_url ? (
                          <a
                            href={data.github_tag_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              fontFamily: 'var(--crown-font-mono)',
                              fontSize: 12,
                              color: 'var(--crown-brand)',
                              textDecoration: 'none',
                            }}
                          >
                            {data.prod_deploy_tag}
                          </a>
                        ) : (
                          <code style={{ fontSize: 12, color: 'var(--crown-muted)' }}>
                            {data.prod_deploy_tag}
                          </code>
                        )}
                      </td>
                    </tr>
                  )}
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Repo</td>
                    <td>
                      <a
                        href={`https://github.com/${data.github_repo}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: 'var(--crown-brand)', fontSize: 13, textDecoration: 'none' }}
                      >
                        {data.github_repo}
                      </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            )}
          </CrownCard>
        </Col>

        <Col span={6}>
          <CrownCard
            title="Authoring Gates"
            right={data ? <Pill color="green">{data.meta_gates?.length ?? 0} active</Pill> : null}
          >
            {loading && <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>Fetching</p>}
            {error && <p style={{ color: 'var(--crown-danger)', fontSize: 13 }}>Unavailable</p>}
            {data?.meta_gates?.map((gate) => (
              <div
                key={gate.id}
                style={{ padding: '8px 0', borderBottom: '1px solid var(--crown-border)' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ color: 'var(--crown-ok)', fontSize: 15 }}>[ok]</span>
                  <span style={{
                    fontFamily: 'var(--crown-font-mono)',
                    fontSize: 12,
                    color: 'var(--crown-ink)',
                    fontWeight: 600,
                  }}>
                    {gate.id}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--crown-muted)' }}>
                    PR #{gate.added_pr}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--crown-muted)', paddingLeft: 24 }}>
                  {gate.description}
                </div>
              </div>
            ))}
          </CrownCard>
        </Col>

        <Col span={12}>
          <CrownCard
            title="Known CI Checks"
            right={data ? (
              <Pill color="green">{data.required_checks?.length ?? 0} listed</Pill>
            ) : null}
          >
            {loading && <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>Fetching</p>}
            {error && <p style={{ color: 'var(--crown-danger)', fontSize: 13 }}>Unavailable</p>}
            {data?.required_checks && (
              <div style={{ columns: 2, columnGap: 32 }}>
                {data.required_checks.map((name) => (
                  <CheckRow key={name} label={name} ok />
                ))}
              </div>
            )}
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
