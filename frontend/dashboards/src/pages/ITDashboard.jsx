import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

/* ── Auth helpers ─────────────────────────────────────────────────────── */
function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token:    sessionStorage.getItem('crown.jwt.access') || '',
      schoolId: sessionStorage.getItem('crown.school.id')  || '',
    };
  } catch { return { token: '', schoolId: '' }; }
}

/* ── Static demo fallback ─────────────────────────────────────────────── */
const DEMO = {
  api_status:      'ok',
  db_status:       'ok',
  last_deploy_tag: 'prod-deploy-2026-02-22-1415',
  last_deploy_sha: 'd196ab66',
  open_tickets:    5,
  overdue_tickets: 1,
  total_devices:   148,
  devices_compliant: 141,
  devices_non_compliant: 7,
  cert_expiry_days: 42,
  failed_checks:   0,
  alerts: [
    { label: 'SSL cert expires in 42 days',         severity: 'yellow' },
    { label: '7 devices out of compliance',         severity: 'yellow' },
    { label: 'Open ticket older than 14 days (×1)', severity: 'red'    },
  ],
};

async function fetchITMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/it/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: DEMO };
  }
}

/* ── Helpers ──────────────────────────────────────────────────────────── */
const PILL_COLORS = {
  red:    { background: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
  yellow: { background: '#fef9c3', color: '#854d0e', border: '#fde047' },
  green:  { background: '#dcfce7', color: '#166534', border: '#86efac' },
  gray:   { background: '#f3f4f6', color: '#374151', border: '#d1d5db' },
};
function Pill({ color = 'gray', children }) {
  const s = PILL_COLORS[color] || PILL_COLORS.gray;
  return (
    <span style={{
      display: 'inline-block', padding: '1px 8px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, border: `1px solid ${s.border}`,
      background: s.background, color: s.color, letterSpacing: 0.2,
    }}>{children}</span>
  );
}

function StatusDot({ status }) {
  const ok = status === 'ok';
  return (
    <span style={{
      display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
      background: ok ? '#22c55e' : '#ef4444', marginRight: 6, flexShrink: 0,
    }} />
  );
}

/* ── Main component ───────────────────────────────────────────────────── */
export default function ITDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchITMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts = data.alerts || DEMO.alerts;
  const compliantPct = data.total_devices
    ? Math.round((data.devices_compliant / data.total_devices) * 100)
    : 0;

  return (
    <CrownLayout
      title="IT Director"
      subtitle="System health, infrastructure, and device management"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      {/* ── KPI row ── */}
      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Open Tickets" value={data.open_tickets ?? DEMO.open_tickets} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Overdue Tickets" value={data.overdue_tickets ?? DEMO.overdue_tickets} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Total Devices" value={data.total_devices ?? DEMO.total_devices} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Cert Expiry (days)" value={data.cert_expiry_days ?? DEMO.cert_expiry_days} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── System Status ── */}
        <Col span={6}>
          <CrownCard title="System Status">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'API',      status: data.api_status ?? DEMO.api_status },
                { label: 'Database', status: data.db_status  ?? DEMO.db_status  },
              ].map(({ label, status }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', fontSize: 13 }}>
                    <StatusDot status={status} />{label}
                  </span>
                  <Pill color={status === 'ok' ? 'green' : 'red'}>{status === 'ok' ? 'OK' : 'ERROR'}</Pill>
                </div>
              ))}
              <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4, borderTop: '1px solid #f3f4f6', paddingTop: 8 }}>
                Last deploy: <strong>{data.last_deploy_tag ?? DEMO.last_deploy_tag}</strong>
                <br />SHA: <code style={{ fontSize: 10 }}>{data.last_deploy_sha ?? DEMO.last_deploy_sha}</code>
              </div>
            </div>
          </CrownCard>
        </Col>

        {/* ── Device Compliance ── */}
        <Col span={6}>
          <CrownCard title="Device / Compliance Summary">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: 'Compliant',     value: data.devices_compliant     ?? DEMO.devices_compliant,     pct: compliantPct, color: '#22c55e' },
                { label: 'Non-Compliant', value: data.devices_non_compliant ?? DEMO.devices_non_compliant, pct: 100 - compliantPct, color: '#ef4444' },
              ].map(({ label, value, pct, color }) => (
                <div key={label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                    <span style={{ color: '#6b7280' }}>{label}</span>
                    <strong>{value}</strong>
                  </div>
                  <div style={{ height: 6, borderRadius: 4, background: '#f3f4f6', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4 }} />
                  </div>
                </div>
              ))}
              <p style={{ margin: '8px 0 0', fontSize: 12, color: '#6b7280' }}>
                {compliantPct}% of {data.total_devices ?? DEMO.total_devices} devices compliant
              </p>
            </div>
          </CrownCard>
        </Col>

        {/* ── Open Tickets ── */}
        <Col span={6}>
          <CrownCard title="Support Tickets">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: 'Total Open',   value: data.open_tickets    ?? DEMO.open_tickets,    color: '#3b82f6' },
                { label: 'Overdue',      value: data.overdue_tickets  ?? DEMO.overdue_tickets,  color: '#ef4444' },
                { label: 'Failed Checks',value: data.failed_checks   ?? DEMO.failed_checks,   color: '#f59e0b' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                  <span style={{ color: '#6b7280' }}>{label}</span>
                  <strong style={{ color }}>{value}</strong>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={6}>
          <CrownCard title="Alerts &amp; Attention">
            {alerts.length === 0
              ? <p style={{ fontSize: 13, color: '#22c55e' }}>No active alerts — all clear.</p>
              : alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Pill color={a.severity}>{a.severity.toUpperCase()}</Pill>
                    <span style={{ fontSize: 13, color: '#374151' }}>{a.label}</span>
                  </div>
                ))
            }
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
