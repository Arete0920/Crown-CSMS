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
  sessions_this_month: 6, staff_hours_logged: 142, certifications_expiring: 4, satisfaction_avg: 4.3,
  snapshot_date: 'Feb 26, 2026',
  upcoming_sessions: [
    { title: 'Google Classroom Deep Dive', date: 'Mar 4',  facilitator: 'T. Hughes',    registered: 18, status: 'upcoming'    },
    { title: 'Differentiated Instruction', date: 'Mar 11', facilitator: 'Guest  CASEL',registered: 22, status: 'upcoming'    },
    { title: 'Crisis Response Refresher',  date: 'Mar 18', facilitator: 'Admin Team',    registered: 34, status: 'upcoming'    },
    { title: 'Gradebook & Rubric Best Practices', date: 'Feb 20', facilitator: 'L. Park', registered: 28, status: 'completed' },
  ],
  certifications: [
    { name: 'CPR / First Aid',       staff_count: 47, expiring_90d: 3 },
    { name: 'Mandated Reporter',     staff_count: 47, expiring_90d: 1 },
    { name: 'SPED Endorsement',      staff_count: 12, expiring_90d: 0 },
    { name: 'Safety Certification',  staff_count: 31, expiring_90d: 0 },
  ],
  completion_by_dept: [
    { dept: 'Upper School Faculty', pct: 92 },
    { dept: 'Middle School Faculty',pct: 88 },
    { dept: 'Admin Staff',          pct: 100 },
    { dept: 'Support Staff',        pct: 74 },
    { dept: 'Coaches / Coaches',    pct: 61 },
  ],
  alerts: [
    { label: '3 staff CPR certifications expiring by Apr 1',   severity: 'red'    },
    { label: '1 mandated reporter cert renewal overdue',       severity: 'red'    },
    { label: 'Spring PD survey closes Mar 5',                  severity: 'yellow' },
  ],
};

async function fetchPDMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/pd/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_MAP = { completed: 'green', upcoming: 'blue', cancelled: 'red', 'in progress': 'yellow' };

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

/*  Professional Development KPI flip cards  */
const ADMIN_KPI = [
  { label: "Trainings This Mo",  value: "5",   trend: null,              trendUp: null,
    definition: "Professional development sessions scheduled or completed this month.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Staff Completed",    value: "78%", trend: "+12% vs last mo", trendUp: true,
    definition: "Percentage of required staff who have completed mandatory PD for this term.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Hours Logged",       value: "184", trend: null,              trendUp: null,
    definition: "Total professional development contact hours logged by all staff this year.",
    dataSource: "PD Module", dataHref: "/pd" },
  { label: "Plans Active",       value: "12",  trend: null,              trendUp: null,
    definition: "Individualized professional growth plans with active goals this year.",
    dataSource: "PD Module", dataHref: "/pd" },
];
export default function PDDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchPDMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const sessions  = Array.isArray(data.upcoming_sessions) ? data.upcoming_sessions : DEMO.upcoming_sessions;
  const upcomingCount = Array.isArray(data.upcoming_sessions)
    ? data.upcoming_sessions.length
    : (data.upcoming_sessions ?? DEMO.sessions_this_month);
  const certs     = data.certifications      || DEMO.certifications;
  const deptComp  = data.completion_by_dept  || DEMO.completion_by_dept;
  const alerts    = data.alerts              || DEMO.alerts;

  return (
    <CrownLayout
      title="PD / Staff Development"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Total Sessions"           value={data.total_sessions          ?? DEMO.sessions_this_month}    /></Col>
          <Col span={3}><CrownMetricCard label="Upcoming"                 value={upcomingCount}                                                /></Col>
          <Col span={3}><CrownMetricCard label="Completed"                value={data.completed_sessions      ?? 0}                           /></Col>
          <Col span={3}><CrownMetricCard label="Avg Satisfaction Score"   value={`${data.average_rating ?? DEMO.satisfaction_avg}/5`} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Sessions & Certifications">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Upcoming Sessions">
              <div style={{ width: '100%', maxWidth: '100%', overflowX: 'auto' }}>
                <table style={{ width: '100%', minWidth: 680, borderCollapse: 'collapse' }}>
                  <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Session', 'Date', 'Facilitator', 'Registered', 'Status'].map(h => <th key={h} style={TH}>{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {sessions.map((s, i) => (
                      <tr key={i}>
                        <td style={TD}>{s.title}</td>
                        <td style={{ ...TD, color: 'var(--crown-muted)', whiteSpace: 'nowrap' }}>{s.date}</td>
                        <td style={{ ...TD, color: 'var(--crown-muted)' }}>{s.facilitator}</td>
                        <td style={{ ...TD, fontWeight: 600 }}>{s.registered}</td>
                        <td style={TD}><Pill color={STATUS_MAP[s.status] || 'gray'}>{s.status}</Pill></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Certification Tracker">
              <div style={{ width: '100%', maxWidth: '100%', overflowX: 'auto' }}>
                <table style={{ width: '100%', minWidth: 420, borderCollapse: 'collapse' }}>
                  <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Cert', 'Staff', 'Expiring (90d)'].map(h => <th key={h} style={TH}>{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {certs.map((c, i) => (
                      <tr key={i}>
                        <td style={TD}>{c.name}</td>
                        <td style={TD}>{c.staff_count}</td>
                        <td style={{ ...TD, fontWeight: 700, color: c.expiring_90d > 0 ? 'var(--crown-danger)' : 'var(--crown-ok)' }}>{c.expiring_90d}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Completion & Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Staff Completion by Department">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {deptComp.map((d, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)' }}>{d.dept}</span>
                      <span style={{ fontWeight: 700, color: d.pct >= 80 ? 'var(--crown-ok)' : 'var(--crown-warn)' }}>{d.pct}%</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.min(d.pct, 100)}%`, height: '100%', background: d.pct >= 80 ? 'var(--crown-ok)' : 'var(--crown-warn)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
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
