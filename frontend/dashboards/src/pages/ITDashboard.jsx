import { useState, useEffect } from 'react';
import CrownLayout   from '../components/crown/CrownLayout.jsx';
import CrownCard     from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection   from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

/*  Auth helpers  */
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

/*  Static demo fallback  */
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
    { label: 'Open ticket older than 14 days (1)', severity: 'red'    },
  ],
};

async function fetchITMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/it/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: DEMO };
  }
}

/*  Helpers  */
function Pill({ color = 'gray', children }) {
  const map = {
    red:    { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)'  },
    yellow: { bg: 'var(--crown-warn-bg)',   fg: 'var(--crown-warn)'    },
    green:  { bg: 'var(--crown-ok-bg)',     fg: 'var(--crown-ok)'      },
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

function StatusDot({ status }) {
  const ok = status === 'ok';
  return (
    <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
      background: ok ? 'var(--crown-ok)' : 'var(--crown-danger)', marginRight: 6, flexShrink: 0,
    }} />
  );
}

/*  Main component  */
/*  IT KPI flip cards  */
const ADMIN_KPI = [
  { label: "Tickets Open",   value: "12",     trend: "-4 vs last wk",   trendUp: true,
    definition: "Open helpdesk tickets assigned to IT staff awaiting resolution.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "Resolved MTD",   value: "47",     trend: "+8 vs last mo",   trendUp: true,
    definition: "Helpdesk tickets resolved and closed this calendar month.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "Assets Tracked", value: "243",    trend: null,               trendUp: null,
    definition: "Technology assets (devices, licenses, AV equipment) in the asset registry.",
    dataSource: "IT Module", dataHref: "/it" },
  { label: "System Uptime",  value: "99.8%",  trend: null,               trendUp: null,
    definition: "Rolling 30-day uptime across all monitored Crown platform services.",
    dataSource: "IT Module", dataHref: "/it" },
];
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
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      {/*  Section 1: Overview KPIs  */}
      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}>
            <CrownMetricCard label="Open Tickets"       value={data.open_tickets       ?? DEMO.open_tickets} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Overdue Tickets"    value={data.overdue_tickets    ?? DEMO.overdue_tickets} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Total Devices"      value={data.total_devices      ?? DEMO.total_devices} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Cert Expiry (days)" value={data.cert_expiry_days   ?? DEMO.cert_expiry_days} />
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/*  Section 2: System Status & Devices  */}
      <DashboardSection title="System Status & Devices">
        <CrownGrid>
          {/* System Status */}
          <Col span={6}>
            <CrownCard title="System Status">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { label: 'API',      status: data.api_status ?? DEMO.api_status },
                  { label: 'Database', status: data.db_status  ?? DEMO.db_status  },
                ].map(({ label, status }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', fontSize: 13, color: 'var(--crown-ink)' }}>
                      <StatusDot status={status} />{label}
                    </span>
                    <Pill color={status === 'ok' ? 'green' : 'red'}>{status === 'ok' ? 'OK' : 'ERROR'}</Pill>
                  </div>
                ))}
                <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4, borderTop: '1px solid var(--crown-border)', paddingTop: 8 }}>
                  Last deploy: <strong>{data.last_deploy_tag ?? DEMO.last_deploy_tag}</strong>
                  <br />SHA: <code style={{ fontSize: 10 }}>{data.last_deploy_sha ?? DEMO.last_deploy_sha}</code>
                </div>
              </div>
            </CrownCard>
          </Col>

          {/* Device Compliance */}
          <Col span={6}>
            <CrownCard title="Device / Compliance Summary">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'Compliant',     value: data.devices_compliant     ?? DEMO.devices_compliant,     pct: compliantPct,         cssColor: 'var(--crown-ok)'     },
                  { label: 'Non-Compliant', value: data.devices_non_compliant ?? DEMO.devices_non_compliant, pct: 100 - compliantPct,   cssColor: 'var(--crown-danger)' },
                ].map(({ label, value, pct, cssColor }) => (
                  <div key={label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                      <span style={{ color: 'var(--crown-muted)' }}>{label}</span>
                      <strong>{value}</strong>
                    </div>
                    <div style={{ height: 6, borderRadius: 4, background: 'var(--crown-surface-2)', overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.max(0, Math.min(pct, 100))}%`, height: '100%', background: cssColor, borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
                <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--crown-muted)' }}>
                  {compliantPct}% of {data.total_devices ?? DEMO.total_devices} devices compliant
                </p>
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/*  Section 3: Tickets & Alerts  */}
      <DashboardSection title="Tickets & Alerts">
        <CrownGrid>
          {/* Support Tickets */}
          <Col span={6}>
            <CrownCard title="Support Tickets">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'Total Open',    value: data.open_tickets    ?? DEMO.open_tickets,    cssColor: 'var(--crown-brand)'  },
                  { label: 'Overdue',       value: data.overdue_tickets ?? DEMO.overdue_tickets, cssColor: 'var(--crown-danger)' },
                  { label: 'Failed Checks', value: data.failed_checks   ?? DEMO.failed_checks,   cssColor: 'var(--crown-warn)'   },
                ].map(({ label, value, cssColor }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                    <span style={{ color: 'var(--crown-muted)' }}>{label}</span>
                    <strong style={{ color: cssColor }}>{value}</strong>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>

          {/* Alerts */}
          <Col span={6}>
            <CrownCard title="Alerts &amp; Attention">
              {alerts.length === 0
                ? <p style={{ fontSize: 13, color: 'var(--crown-ok)' }}>No active alerts  all clear.</p>
                : <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {alerts.map((a, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                        background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                        border: '1px solid var(--crown-border)',
                      }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                          background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                        <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                      </div>
                    ))}
                  </div>
              }
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
