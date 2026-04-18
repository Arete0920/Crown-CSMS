import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return { token: sessionStorage.getItem('crown.jwt.access') || '', schoolId: sessionStorage.getItem('crown.school.id') || '' };
  } catch { return { token: '', schoolId: '' }; }
}

const DEMO = {
  lunch_balance_alerts: 31, unpaid_balances_total: 1140, applications_pending: 7, services_active: 89,
  snapshot_date: 'Feb 26, 2026',
  balance_alerts_by_grade: [
    { grade: '7',  below_five: 4, at_zero: 1, severity: 'warning'  },
    { grade: '8',  below_five: 6, at_zero: 2, severity: 'critical' },
    { grade: '9',  below_five: 5, at_zero: 1, severity: 'warning'  },
    { grade: '10', below_five: 7, at_zero: 3, severity: 'critical' },
    { grade: '11', below_five: 4, at_zero: 0, severity: 'info'     },
    { grade: '12', below_five: 5, at_zero: 1, severity: 'warning'  },
  ],
  services_by_type: [
    { type: 'Free & Reduced Lunch', count: 48, pct: 94 },
    { type: 'ESL / ELL Support',    count: 12, pct: 24 },
    { type: 'SPED (IEP/504)',       count: 17, pct: 33 },
    { type: 'Counseling Services',  count: 24, pct: 47 },
    { type: 'Extended Care',        count: 22, pct: 43 },
  ],
  pending_applications: [
    { service_type: 'Free & Reduced Lunch', count: 4, oldest_days: 9  },
    { service_type: 'Financial Aid',        count: 2, oldest_days: 14 },
    { service_type: 'Counseling Services',  count: 1, oldest_days: 5  },
  ],
  alerts: [
    { label: '31 student lunch balances below $5  parent notifications pending', severity: 'red'    },
    { label: '7 unresolved service applications older than 5 days',               severity: 'yellow' },
    { label: 'Free & Reduced Lunch deadline  Mar 31',                             severity: 'yellow' },
  ],
};

/*  Student Services KPI flip cards  */
const SS_KPI = [
  { label: "Balance Alerts",  value: "31",     trend: "needs action",   trendUp: false,
    definition: "Students with a lunch account balance below $5  parent notifications are pending.",
    dataSource: "Student Services", dataHref: "/student-services" },
  { label: "Services Active", value: "89",     trend: null,             trendUp: null,
    definition: "Students currently enrolled in at least one school support service this term.",
    dataSource: "Student Services", dataHref: "/student-services" },
  { label: "Apps Pending",    value: "7",      trend: "5+ days old",    trendUp: false,
    definition: "Service applications awaiting review  oldest is 14 days, action required.",
    dataSource: "Student Services", dataHref: "/student-services" },
  { label: "Unpaid Balances", value: "$1,140", trend: null,             trendUp: null,
    definition: "Total outstanding unpaid obligations across all student service accounts.",
    dataSource: "Student Services", dataHref: "/student-services" },
];

async function fetchStudentServicesMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/student-services/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const SEV_MAP = { critical: 'red', warning: 'yellow', info: 'blue' };

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

const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

export default function StudentServicesDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchStudentServicesMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const balanceAlerts = data.balance_alerts_by_grade || DEMO.balance_alerts_by_grade;
  const serviceTypes  = data.services_by_type        || DEMO.services_by_type;
  const pendingApps   = data.pending_applications    || DEMO.pending_applications;
  const alerts        = data.alerts                  || DEMO.alerts;
  const maxCount      = Math.max(...serviceTypes.map(s => s.count), 1);

  return (
    <CrownLayout
      title="Student Services"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={SS_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Lunch Balance Alerts" value={data.lunch_balance_alerts    ?? DEMO.lunch_balance_alerts}    /></Col>
          <Col span={3}><CrownMetricCard label="Unpaid Balances"       value={`$${data.unpaid_balances_total ?? DEMO.unpaid_balances_total}`} /></Col>
          <Col span={3}><CrownMetricCard label="Applications Pending"  value={data.applications_pending   ?? DEMO.applications_pending}   /></Col>
          <Col span={3}><CrownMetricCard label="Active Services"        value={data.services_active        ?? DEMO.services_active}        /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Balance Alerts & Active Services">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Lunch Balance Alerts by Grade">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Grade', 'Below $5', 'At $0', 'Severity'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {balanceAlerts.map((g, i) => (
                    <tr key={i} style={{ background: g.severity === 'critical' ? 'var(--crown-danger-bg)' : '' }}>
                      <td style={TD}>Grade {g.grade}</td>
                      <td style={{ ...TD, fontWeight: 700 }}>{g.below_five}</td>
                      <td style={{ ...TD, fontWeight: 700, color: g.at_zero > 0 ? 'var(--crown-danger)' : 'inherit' }}>{g.at_zero}</td>
                      <td style={TD}><Pill color={SEV_MAP[g.severity] || 'gray'}>{g.severity}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Active Services by Type">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {serviceTypes.map((s, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)' }}>{s.type}</span>
                      <span style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{s.count} students</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.round((s.count / maxCount) * 100)}%`, height: '100%', background: 'var(--crown-brand)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Pending Applications & Alerts">
        <CrownGrid>
          <Col span={5}>
            <CrownCard title="Pending Applications">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Service Type', 'Count', 'Oldest (days)'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {pendingApps.map((a, i) => (
                    <tr key={i}>
                      <td style={TD}>{a.service_type}</td>
                      <td style={{ ...TD, fontWeight: 700 }}>{a.count}</td>
                      <td style={{ ...TD, fontWeight: 700, color: a.oldest_days >= 10 ? 'var(--crown-danger)' : 'var(--crown-warn)' }}>{a.oldest_days}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={7}>
            <CrownCard title="Alerts">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: a.severity === 'red' ? 'var(--crown-danger-bg)' : 'var(--crown-warn-bg)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: a.severity === 'red' ? 'var(--crown-danger)' : 'var(--crown-warn)' }} />
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
