import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
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
  students_on_iep: 47,
  upcoming_reviews: 9,
  accommodations_active: 112,
  referrals_pending: 4,
  snapshot_date: 'Feb 26, 2026',
  iep_reviews: [
    { student_id: 'STU-1042', type: 'Annual Review', due_date: 'Mar 1',  status: 'pending'   },
    { student_id: 'STU-0837', type: '3-Year Eval',   due_date: 'Mar 5',  status: 'scheduled' },
    { student_id: 'STU-2211', type: 'Annual Review', due_date: 'Mar 10', status: 'active'    },
    { student_id: 'STU-0094', type: 'Initial IEP',   due_date: 'Mar 14', status: 'flagged'   },
  ],
  accommodations_by_grade: [
    { grade: '7',  count: 14, pct: 58 },
    { grade: '8',  count: 18, pct: 75 },
    { grade: '9',  count: 22, pct: 92 },
    { grade: '10', count: 20, pct: 83 },
    { grade: '11', count: 19, pct: 79 },
    { grade: '12', count: 19, pct: 79 },
  ],
  caseload: [
    { specialist: 'M. Torres',   active_plans: 18, pending_reviews: 2 },
    { specialist: 'J. Huang',    active_plans: 16, pending_reviews: 4 },
    { specialist: 'R. Williams', active_plans: 13, pending_reviews: 3 },
  ],
  alerts: [
    { label: '4 IEP reviews overdue — action required',        severity: 'red'    },
    { label: '9 annual reviews due within 30 days',            severity: 'yellow' },
    { label: '3 transition plans pending specialist review',   severity: 'yellow' },
  ],
};

async function fetchAcademicSupportMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/academic-support/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
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
const STATUS_PILL = { active: 'green', scheduled: 'blue', pending: 'yellow', flagged: 'red', closed: 'gray' };
const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

/* â”€â”€ Academic Support KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Students in Support", value: "24", trend: null,              trendUp: null,
    definition: "Students currently enrolled in at least one academic support or intervention program.",
    dataSource: "Academics Module", dataHref: "/academics" },
  { label: "Sessions This Week",  value: "38", trend: null,              trendUp: null,
    definition: "Total one-on-one or small group support sessions scheduled or completed this week.",
    dataSource: "Academic Support Module", dataHref: "/academic-support" },
  { label: "Avg GPA Improvement", value: "+0.4",trend: null,             trendUp: null,
    definition: "Mean GPA improvement for students who have been in the support program this term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
  { label: "Accommodation Plans", value: "15", trend: null,              trendUp: null,
    definition: "Active IEP, 504, or accommodation plans on file for supported students.",
    dataSource: "Academic Support Module", dataHref: "/academic-support" },
];
export default function AcademicSupportDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchAcademicSupportMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const iepReviews  = data.iep_reviews            || DEMO.iep_reviews;
  const accomGrades = data.accommodations_by_grade || DEMO.accommodations_by_grade;
  const caseload    = data.caseload                || DEMO.caseload;
  const alerts      = data.alerts                  || DEMO.alerts;

  return (
    <CrownLayout
      title="Academic Support / SPED"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading…</p>}

      {/* ── Overview KPIs ── */}
      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Students on IEP"       value={data.students_on_iep       ?? DEMO.students_on_iep}       /></Col>
          <Col span={3}><CrownMetricCard label="Reviews Due (30 days)" value={data.upcoming_reviews      ?? DEMO.upcoming_reviews}      /></Col>
          <Col span={3}><CrownMetricCard label="Active Accommodations"  value={data.accommodations_active ?? DEMO.accommodations_active}  /></Col>
          <Col span={3}><CrownMetricCard label="Referrals Pending"      value={data.referrals_pending     ?? DEMO.referrals_pending}      /></Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── IEP Tracking & Caseload ── */}
      <DashboardSection title="IEP Reviews & Caseload">
        <CrownGrid>
          <Col span={7}>
            <CrownCard title="IEP Review Calendar">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Student ID', 'Type', 'Due Date', 'Status'].map(h => <th key={h} style={TH}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {iepReviews.map((r, i) => (
                    <tr key={i}>
                      <td style={TD}>{r.student_id}</td>
                      <td style={TD}>{r.type}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{r.due_date}</td>
                      <td style={TD}><Pill color={STATUS_PILL[r.status] || 'gray'}>{r.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={5}>
            <CrownCard title="Caseload Summary">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Specialist', 'Plans', 'Pending'].map(h => <th key={h} style={TH}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {caseload.map((c, i) => (
                    <tr key={i}>
                      <td style={TD}>{c.specialist}</td>
                      <td style={TD}>{c.active_plans}</td>
                      <td style={{ ...TD, fontWeight: 700, color: c.pending_reviews > 3 ? 'var(--crown-danger)' : 'var(--crown-ok)' }}>{c.pending_reviews}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Accommodations & Alerts ── */}
      <DashboardSection title="Accommodations & Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Active Accommodations by Grade">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {accomGrades.map((g, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)' }}>Grade {g.grade}</span>
                      <span style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{g.count}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.min(g.pct, 100)}%`, height: '100%', background: 'var(--crown-brand)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts & Action Items">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
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
