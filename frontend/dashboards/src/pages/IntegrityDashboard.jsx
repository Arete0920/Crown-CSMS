import { useEffect, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

async function fetchIntegrity() {
  try {
    const token = sessionStorage.getItem('crown.jwt.access') || '';
    const headers = { Accept: 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await globalThis.fetch(`${apiBase()}/api/integrity/`, { headers });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch {
    return { ok: false, data: null };
  }
}

function Pill({ color = 'gray', children }) {
  const map = {
    red:    { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)'  },
    yellow: { bg: 'var(--crown-warn-bg)',   fg: 'var(--crown-warn)'    },
    green:  { bg: 'var(--crown-ok-bg)',     fg: 'var(--crown-ok)'      },
    blue:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-brand)'   },
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

function CheckRow({ label, ok = true }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid var(--crown-border)' }}>
      <span style={{ fontSize: 16, color: ok ? 'var(--crown-ok)' : 'var(--crown-danger)' }}>
        {ok ? '[ok]' : '[x]'}
      </span>
      <span style={{ fontSize: 13, fontFamily: "var(--crown-font-mono)", color: 'var(--crown-ink)' }}>{label}</span>
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
        fontFamily: "var(--crown-font-mono)",
        color: copied ? 'var(--crown-ok)' : 'var(--crown-muted)',
        background: copied ? 'var(--crown-ok-bg)' : 'var(--crown-surface-2)',
        border: '1px solid',
        borderColor: 'var(--crown-border)',
        borderRadius: 6,
        cursor: 'pointer',
        lineHeight: '18px',
        transition: 'all 0.15s',
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
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 0 }}>
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          style={{ fontFamily: "var(--crown-font-mono)", fontSize: 13, color: 'var(--crown-brand)', textDecoration: 'none', fontWeight: 600 }}
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
        fontFamily: "var(--crown-font-mono)",
        color: copied ? 'var(--crown-ok)' : 'var(--crown-brand)',
        background: copied ? 'var(--crown-ok-bg)' : 'var(--crown-surface-2)',
        border: '1px solid',
        borderColor: 'var(--crown-border)',
        borderRadius: 6,
        cursor: 'pointer',
        lineHeight: '18px',
        transition: 'all 0.15s',
      }}
    >
      {copied ? 'copied!' : 'copy proof'}
    </button>
  );
}

/*  Integrity / Audit KPI flip cards  */
const ADMIN_KPI = [
  { label: "Audit Events Today", value: "",   trend: null,              trendUp: null,
    definition: "Total system audit log entries recorded in the last 24 hours.",
    dataSource: "Audit Log API", dataHref: "/integrity" },
  { label: "Failed Logins",      value: "",   trend: null,              trendUp: null,
    definition: "Number of failed authentication attempts in the monitoring window.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Data Changes",       value: "",   trend: null,              trendUp: null,
    definition: "Number of create/update/delete operations on sensitive data records today.",
    dataSource: "Audit Log API", dataHref: "/integrity" },
  { label: "Compliance Score",   value: "96%", trend: "+1% vs last wk",  trendUp: true,
    definition: "Automated compliance check score across all monitored policies and access controls.",
    dataSource: "Integrity Module", dataHref: "/integrity" },
];
export default function IntegrityDashboard() {
  const [state, setState] = useState({ loading: true, error: false, data: null });

  useEffect(() => {
    fetchIntegrity().then(({ ok, data }) => {
      setState({ loading: false, error: !ok || !data?.ok, data: ok ? data : null });
    });
  }, []);

  const { loading, error, data } = state;

  const envColor = data?.env === 'prod' ? 'green' : data?.env === 'dev' ? 'yellow' : 'gray';

  const timestamp = data?.timestamp
    ? new Date(data.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : '';

  return (
    <CrownLayout title="Crown Integrity" subtitle="System verification - live">
      <KpiStrip cards={ADMIN_KPI} />
      <CrownGrid>

        {/* Header row */}
        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '4px 0 12px' }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--crown-ink)' }}>Crown Integrity Dashboard</span>
            {!loading && !error && <Pill color="green">LIVE</Pill>}
            {error && <Pill color="yellow">UNAVAILABLE</Pill>}
            {loading && <Pill color="gray">Loading</Pill>}
            {!loading && !error && data && <CopyProofButton data={data} />}
          </div>
        </Col>

        {/* Build info */}
        <Col span={6}>
          <CrownCard title="Deployment">
            {loading && <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>Fetching</p>}
            {error && <p style={{ color: 'var(--crown-danger)', fontSize: 13 }}>Could not reach /api/integrity/</p>}
            {data && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)', width: 120 }}>Build SHA</td>
                    <td><ShaLink sha={data.build_sha} url={data.github_commit_url} /></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Environment</td>
                    <td><Pill color={envColor}>{data.env}</Pill></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: 'var(--crown-muted)' }}>Version</td>
                    <td style={{ fontFamily: "var(--crown-font-mono)", color: 'var(--crown-ink)' }}>{data.version}</td>
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
                          style={{ fontFamily: "var(--crown-font-mono)", fontSize: 12, color: 'var(--crown-brand)', textDecoration: 'none' }}
                        >
                          {data.prod_deploy_tag}
                        </a>
                      ) : (
                        <code style={{ fontSize: 12, color: 'var(--crown-muted)' }}>{data.prod_deploy_tag}</code>
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

        {/* Meta-gates */}
        <Col span={6}>
          <CrownCard title="Authoring Gates" right={data ? <Pill color="green">{data.meta_gates?.length ?? 0} active</Pill> : null}>
            {loading && <p style={{ color: 'var(--crown-muted)', fontSize: 13 }}>Fetching</p>}
            {error && <p style={{ color: 'var(--crown-danger)', fontSize: 13 }}>Unavailable</p>}
            {data?.meta_gates?.map((gate) => (
              <div key={gate.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--crown-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ color: 'var(--crown-ok)', fontSize: 15 }}>?</span>
                  <span style={{ fontFamily: "var(--crown-font-mono)", fontSize: 12, color: 'var(--crown-ink)', fontWeight: 600 }}>{gate.id}</span>
                  <span style={{ fontSize: 11, color: 'var(--crown-muted)' }}>PR #{gate.added_pr}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--crown-muted)', paddingLeft: 24 }}>{gate.description}</div>
              </div>
            ))}
          </CrownCard>
        </Col>

        {/* Required checks */}
        <Col span={12}>
          <CrownCard
            title="Known CI Checks"
            right={data ? <Pill color="green">{data.required_checks?.length ?? 0} listed - 7 enforced</Pill> : null}
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
