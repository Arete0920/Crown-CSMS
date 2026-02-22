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
  staff_absent_today:       3,
  coverage_gaps:            1,
  open_requests:            7,
  hr_tasks_due:             4,
  compliance_items_due:     2,
  recent_requests: [
    { label: 'Facility repair — gym HVAC',      status: 'open',       priority: 'high'   },
    { label: 'Supply order — classroom consumables', status: 'pending', priority: 'normal' },
    { label: 'Background check — new hire',     status: 'in_review',  priority: 'high'   },
    { label: 'Leave request — T. Williams',     status: 'approved',   priority: 'normal' },
    { label: 'Vendor invoice — janitorial svc', status: 'pending',    priority: 'normal' },
  ],
  hr_tasks: [
    { label: 'Annual TB test due — 2 staff',      due: 'Feb 28' },
    { label: 'I-9 reverification — 1 staff',      due: 'Mar 5'  },
    { label: 'Handbook acknowledgment — 4 staff', due: 'Mar 10' },
    { label: 'Emergency contact update',           due: 'Mar 15' },
  ],
  alerts: [
    { label: '1 coverage gap today — Period 3 sub needed', severity: 'red'    },
    { label: '2 compliance items due this week',           severity: 'yellow' },
    { label: '3 staff absent — substitutes placed',        severity: 'gray'   },
  ],
};

async function fetchOfficeMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/office/metrics/`;
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

const STATUS_COLOR = {
  open:      'red',
  pending:   'yellow',
  in_review: 'yellow',
  approved:  'green',
  closed:    'gray',
};

/* ── Main component ───────────────────────────────────────────────────── */
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
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      {/* ── KPI row ── */}
      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Staff Absent Today" value={data.staff_absent_today ?? DEMO.staff_absent_today} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Coverage Gaps" value={data.coverage_gaps ?? DEMO.coverage_gaps} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Open Requests" value={data.open_requests ?? DEMO.open_requests} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Compliance Due" value={data.compliance_items_due ?? DEMO.compliance_items_due} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Recent Requests ── */}
        <Col span={6}>
          <CrownCard title="Office Tickets &amp; Requests">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {requests.map((r, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 0', borderBottom: '1px solid #f9fafb', fontSize: 12,
                }}>
                  <span style={{ color: '#374151', flex: 1 }}>{r.label}</span>
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 8 }}>
                    {r.priority === 'high' && <Pill color="red">high</Pill>}
                    <Pill color={STATUS_COLOR[r.status] || 'gray'}>{r.status.replace('_', ' ')}</Pill>
                  </div>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

        {/* ── HR Tasks ── */}
        <Col span={6}>
          <CrownCard title="HR Tasks Due">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {hrTasks.map((t, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 0', borderBottom: '1px solid #f9fafb', fontSize: 12,
                }}>
                  <span style={{ color: '#374151' }}>{t.label}</span>
                  <span style={{ color: '#6b7280', fontWeight: 600, fontSize: 11, flexShrink: 0, marginLeft: 8 }}>Due {t.due}</span>
                </div>
              ))}
              <p style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>
                {data.hr_tasks_due ?? DEMO.hr_tasks_due} total HR tasks require action
              </p>
            </div>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={12}>
          <CrownCard title="Alerts &amp; Compliance">
            {alerts.length === 0
              ? <p style={{ fontSize: 13, color: '#22c55e' }}>No active alerts — operations normal.</p>
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
