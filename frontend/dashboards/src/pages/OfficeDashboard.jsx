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
  staff_absent_today:       3,
  coverage_gaps:            1,
  open_requests:            7,
  hr_tasks_due:             4,
  compliance_items_due:     2,
  recent_requests: [
    { label: 'Facility repair  gym HVAC',      status: 'open',       priority: 'high'   },
    { label: 'Supply order  classroom consumables', status: 'pending', priority: 'normal' },
    { label: 'Background check  new hire',     status: 'in_review',  priority: 'high'   },
    { label: 'Leave request  T. Williams',     status: 'approved',   priority: 'normal' },
    { label: 'Vendor invoice  janitorial svc', status: 'pending',    priority: 'normal' },
  ],
  hr_tasks: [
    { label: 'Annual TB test due  2 staff',      due: 'Feb 28' },
    { label: 'I-9 reverification  1 staff',      due: 'Mar 5'  },
    { label: 'Handbook acknowledgment  4 staff', due: 'Mar 10' },
    { label: 'Emergency contact update',           due: 'Mar 15' },
  ],
  alerts: [
    { label: '1 coverage gap today  Period 3 sub needed', severity: 'red'    },
    { label: '2 compliance items due this week',           severity: 'yellow' },
    { label: '3 staff absent  substitutes placed',        severity: 'gray'   },
  ],
};

async function fetchOfficeMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/office/metrics/`;
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
  open:      'red',
  pending:   'yellow',
  in_review: 'yellow',
  approved:  'green',
  closed:    'gray',
};

/*  Main component  */
/*  Office KPI flip cards  */
const ADMIN_KPI = [
  { label: "Front Desk Visitors", value: "14", trend: null,               trendUp: null,
    definition: "Visitors who have checked in at the main office today.",
    dataSource: "Office Module", dataHref: "/office" },
  { label: "Messages Pending",    value: "7",  trend: null,               trendUp: null,
    definition: "Phone or written messages waiting to be delivered to staff or returned.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Tasks Due Today",     value: "5",  trend: null,               trendUp: null,
    definition: "Administrative tasks assigned to the office team due today.",
    dataSource: "Office Module", dataHref: "/office" },
  { label: "Packages In",         value: "3",  trend: null,               trendUp: null,
    definition: "Deliveries received and logged at the front desk today.",
    dataSource: "Office Module", dataHref: "/office" },
];
export default function OfficeDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchOfficeMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const requests = data.recent_requests || DEMO.recent_requests;
  const hrTasks  = data.hr_tasks        || DEMO.hr_tasks;
  const alerts   = data.alerts          || DEMO.alerts;

  return (
    <CrownLayout
      title="Office &amp; HR"
      subtitle="Staff coverage, HR tasks, requests, and compliance"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Staff Absent Today" value={data.staff_absent_today ?? DEMO.staff_absent_today} /></Col>
          <Col span={3}><CrownMetricCard label="Coverage Gaps" value={data.coverage_gaps ?? DEMO.coverage_gaps} /></Col>
          <Col span={3}><CrownMetricCard label="Open Requests" value={data.open_requests ?? DEMO.open_requests} /></Col>
          <Col span={3}><CrownMetricCard label="Compliance Due" value={data.compliance_items_due ?? DEMO.compliance_items_due} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Requests &amp; Tasks">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Office Tickets &amp; Requests">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {requests.map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '6px 0', borderBottom: '1px solid var(--crown-border)', fontSize: 12,
                  }}>
                    <span style={{ color: 'var(--crown-ink)', flex: 1 }}>{r.label}</span>
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 8 }}>
                      {r.priority === 'high' && <Pill color="red">high</Pill>}
                      <Pill color={STATUS_COLOR[r.status] || 'gray'}>{r.status.replace('_', ' ')}</Pill>
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="HR Tasks Due">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {hrTasks.map((t, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '6px 0', borderBottom: '1px solid var(--crown-border)', fontSize: 12,
                  }}>
                    <span style={{ color: 'var(--crown-ink)' }}>{t.label}</span>
                    <span style={{ color: 'var(--crown-muted)', fontWeight: 600, fontSize: 11, flexShrink: 0, marginLeft: 8 }}>Due {t.due}</span>
                  </div>
                ))}
                <p style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4 }}>
                  {data.hr_tasks_due ?? DEMO.hr_tasks_due} total HR tasks require action
                </p>
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Alerts">
        <CrownGrid>
          <Col span={12}>
            <CrownCard title="Alerts &amp; Compliance">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.length === 0
                  ? <p style={{ fontSize: 13, color: 'var(--crown-ok)' }}>No active alerts  operations normal.</p>
                  : alerts.map((a, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                        background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                        border: '1px solid var(--crown-border)' }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                          background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                        <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                      </div>
                    ))
                }
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
