import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
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
  referrals_this_week:  11,
  active_plans:          8,
  detentions_week:       5,
  suspensions_week:      1,
  recent_referrals: [
    { student: 'Marcus Brown',   grade: '8',  category: 'Disruptive behavior', date: 'Feb 22', counselor: 'J. Okafor', status: 'open' },
    { student: 'Tyler Green',    grade: '10', category: 'Truancy',             date: 'Feb 21', counselor: 'M. Cruz',   status: 'open' },
    { student: 'Aisha Patel',    grade: '9',  category: 'Academic concern',    date: 'Feb 20', counselor: 'J. Okafor', status: 'plan_active' },
    { student: 'Noah Williams',  grade: '7',  category: 'Bullying',            date: 'Feb 19', counselor: 'M. Cruz',   status: 'resolved' },
    { student: 'Chloe Rivera',   grade: '11', category: 'Anxiety / wellness',  date: 'Feb 18', counselor: 'J. Okafor', status: 'plan_active' },
  ],
  behavior_categories: [
    { category: 'Disruptive behavior', count: 4 },
    { category: 'Truancy / late',      count: 3 },
    { category: 'Academic concern',    count: 2 },
    { category: 'Bullying',            count: 1 },
    { category: 'Wellness / anxiety',  count: 1 },
  ],
  caseload_by_counselor: [
    { counselor: 'J. Okafor',  open: 4, plan_active: 3, resolved_mtd: 7 },
    { counselor: 'M. Cruz',    open: 3, plan_active: 2, resolved_mtd: 5 },
  ],
  alerts: [
    { label: '2 follow-up meetings overdue this week',                   severity: 'red'    },
    { label: 'Tyler Green  3rd truancy this semester, parent mtg needed', severity: 'red'    },
    { label: 'Repeat incident: Marcus Brown  2nd referral in 5 days',   severity: 'yellow' },
    { label: '1 suspension pending VP review',                           severity: 'yellow' },
  ],
};

async function fetchCounselingMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/counseling/metrics/`;
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

const STATUS_COLOR = {
  open:         'red',
  plan_active:  'yellow',
  resolved:     'green',
};

/*  Main component  */
/*  Counseling KPI flip cards  */
const ADMIN_KPI = [
  { label: "Students Seen MTD",  value: "18",  trend: null,              trendUp: null,
    definition: "Unique students who had a counseling session this calendar month.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Referrals Open",     value: "4",   trend: null,              trendUp: null,
    definition: "Open referrals awaiting follow-up from the counselor or outside provider.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Plans Active",       value: "12",  trend: null,              trendUp: null,
    definition: "Students with an active counseling, IEP, or 504 support plan.",
    dataSource: "Counseling Module", dataHref: "/counseling" },
  { label: "Academic Risk",      value: "6",   trend: "-2 vs last wk",  trendUp: true,
    definition: "Students flagged at academic risk (GPA below threshold or 3+ missing assignments).",
    dataSource: "Academics Module", dataHref: "/academics" },
];
export default function CounselingDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchCounselingMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts      = data.alerts                  || DEMO.alerts;
  const referrals   = data.recent_referrals        || DEMO.recent_referrals;
  const categories  = data.behavior_categories     || DEMO.behavior_categories;
  const caseloads   = data.caseload_by_counselor   || DEMO.caseload_by_counselor;
  const maxCat      = Math.max(...categories.map(c => c.count), 1);

  return (
    <CrownLayout
      title="Counseling &amp; Discipline"
      subtitle="Referrals, behavior plans, caseload, and follow-up tracking"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Referrals (This Week)" value={data.referrals_this_week ?? DEMO.referrals_this_week} /></Col>
          <Col span={3}><CrownMetricCard label="Active Plans" value={data.active_plans ?? DEMO.active_plans} /></Col>
          <Col span={3}><CrownMetricCard label="Detentions (Week)" value={data.detentions_week ?? DEMO.detentions_week} /></Col>
          <Col span={3}><CrownMetricCard label="Suspensions (Week)" value={data.suspensions_week ?? DEMO.suspensions_week} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Referrals &amp; Categories">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Recent Referrals">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Student', 'Gr', 'Category', 'Date', 'Counselor', 'Status'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {referrals.map((r, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{r.student}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)' }}>{r.grade}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{r.category}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)', whiteSpace: 'nowrap' }}>{r.date}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{r.counselor}</td>
                      <td style={{ padding: '6px 8px' }}>
                        <Pill color={STATUS_COLOR[r.status] || 'gray'}>{r.status.replace('_', ' ')}</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Behavior Categories (Week)">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {categories.map((c, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                      <span style={{ fontWeight: 500, color: 'var(--crown-ink)' }}>{c.category}</span>
                      <span style={{ color: 'var(--crown-muted)' }}>{c.count}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-border)', borderRadius: 4 }}>
                      <div style={{ height: 6, borderRadius: 4, width: `${Math.round((c.count / maxCat) * 100)}%`, background: 'var(--crown-brand)' }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Caseload &amp; Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Case Load by Counselor">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Counselor', 'Open', 'Plan Active', 'Resolved MTD'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {caseloads.map((c, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{c.counselor}</td>
                      <td style={{ padding: '6px 8px' }}><Pill color="red">{c.open}</Pill></td>
                      <td style={{ padding: '6px 8px' }}><Pill color="yellow">{c.plan_active}</Pill></td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ok)', fontWeight: 600 }}>{c.resolved_mtd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts &amp; Follow-Ups">
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
