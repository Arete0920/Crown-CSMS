import { useEffect, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

async function fetchIntegrity() {
  try {
    const token = sessionStorage.getItem('crown.jwt.access') || '';
    const headers = { Accept: 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${apiBase()}/api/integrity/`, { headers });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch {
    return { ok: false, data: null };
  }
}

function Pill({ color, children }) {
  const colors = {
    green:  { background: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' },
    yellow: { background: '#fef9c3', color: '#854d0e', border: '1px solid #fde047' },
    gray:   { background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' },
  };
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      ...colors[color] || colors.gray,
    }}>
      {children}
    </span>
  );
}

function CheckRow({ label, ok = true }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
      <span style={{ fontSize: 16, color: ok ? '#10b981' : '#ef4444' }}>
        {ok ? '✓' : '✗'}
      </span>
      <span style={{ fontSize: 13, fontFamily: 'monospace', color: '#374151' }}>{label}</span>
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
        fontFamily: 'monospace',
        color: copied ? '#065f46' : '#6b7280',
        background: copied ? '#d1fae5' : '#f3f4f6',
        border: '1px solid',
        borderColor: copied ? '#6ee7b7' : '#d1d5db',
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
          style={{ fontFamily: 'monospace', fontSize: 13, color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}
        >
          {short} ↗
        </a>
      ) : (
        <code style={{ fontSize: 13, color: '#6b7280' }}>{short}</code>
      )}
      {isReal && <CopyButton text={sha} />}
    </span>
  );
}

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
    : '—';

  return (
    <CrownLayout title="Crown Integrity" subtitle="System verification — live">
      <CrownGrid>

        {/* Header row */}
        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '4px 0 12px' }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: '#111827' }}>Crown Integrity Dashboard</span>
            {!loading && !error && <Pill color="green">LIVE</Pill>}
            {error && <Pill color="yellow">UNAVAILABLE</Pill>}
            {loading && <Pill color="gray">Loading…</Pill>}
          </div>
        </Col>

        {/* Build info */}
        <Col span={6}>
          <CrownCard title="Deployment">
            {loading && <p style={{ color: '#9ca3af', fontSize: 13 }}>Fetching…</p>}
            {error && <p style={{ color: '#dc2626', fontSize: 13 }}>Could not reach /api/integrity/</p>}
            {data && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280', width: 120 }}>Build SHA</td>
                    <td><ShaLink sha={data.build_sha} url={data.github_commit_url} /></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280' }}>Environment</td>
                    <td><Pill color={envColor}>{data.env}</Pill></td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280' }}>Version</td>
                    <td style={{ fontFamily: 'monospace', color: '#374151' }}>{data.version}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280' }}>Checked at</td>
                    <td style={{ color: '#374151' }}>{timestamp}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280' }}>Deploy tag</td>
                    <td>
                      {data.github_tag_url ? (
                        <a
                          href={data.github_tag_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontFamily: 'monospace', fontSize: 12, color: '#2563eb', textDecoration: 'none' }}
                        >
                          {data.prod_deploy_tag} ↗
                        </a>
                      ) : (
                        <code style={{ fontSize: 12, color: '#6b7280' }}>{data.prod_deploy_tag}</code>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 0', color: '#6b7280' }}>Repo</td>
                    <td>
                      <a
                        href={`https://github.com/${data.github_repo}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: '#2563eb', fontSize: 13, textDecoration: 'none' }}
                      >
                        {data.github_repo} ↗
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
            {loading && <p style={{ color: '#9ca3af', fontSize: 13 }}>Fetching…</p>}
            {error && <p style={{ color: '#dc2626', fontSize: 13 }}>Unavailable</p>}
            {data?.meta_gates?.map((gate) => (
              <div key={gate.id} style={{ padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ color: '#10b981', fontSize: 15 }}>✓</span>
                  <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#374151', fontWeight: 600 }}>{gate.id}</span>
                  <span style={{ fontSize: 11, color: '#9ca3af' }}>PR #{gate.added_pr}</span>
                </div>
                <div style={{ fontSize: 12, color: '#6b7280', paddingLeft: 24 }}>{gate.description}</div>
              </div>
            ))}
          </CrownCard>
        </Col>

        {/* Required checks */}
        <Col span={12}>
          <CrownCard
            title="Required Branch Protection Checks"
            right={data ? <Pill color="green">{data.required_checks?.length ?? 0} required</Pill> : null}
          >
            {loading && <p style={{ color: '#9ca3af', fontSize: 13 }}>Fetching…</p>}
            {error && <p style={{ color: '#dc2626', fontSize: 13 }}>Unavailable</p>}
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
