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
  enrollment_total: 412, pending_requests: 8, transcripts_issued_mtd: 23, holds_active: 3,
  snapshot_date: 'Feb 26, 2026',
  pending_requests_list: [
    { type: 'Enrollment Verification', submitted: 'Feb 20', target_date: 'Feb 27', status: 'in_progress' },
    { type: 'Transcript  College',    submitted: 'Feb 21', target_date: 'Feb 28', status: 'pending'     },
    { type: 'Transcript  College',    submitted: 'Feb 22', target_date: 'Mar 1',  status: 'pending'     },
    { type: 'Records Transfer',        submitted: 'Feb 18', target_date: 'Feb 25', status: 'hold'        },
    { type: 'Name Change Request',     submitted: 'Feb 19', target_date: 'Feb 26', status: 'complete'    },
  ],
  transcript_queue: [
    { destination_type: 'College / University', count: 14, avg_days: 2.3 },
    { destination_type: 'Transfer  Public',    count:  4, avg_days: 1.8 },
    { destination_type: 'Transfer  Private',   count:  3, avg_days: 2.1 },
    { destination_type: 'Court / Legal',        count:  2, avg_days: 5.0 },
  ],
  new_enrollments_by_grade: [
    { grade: '7',  count: 6,  pct: 100 },
    { grade: '8',  count: 4,  pct: 67  },
    { grade: '9',  count: 3,  pct: 50  },
    { grade: '10', count: 2,  pct: 33  },
    { grade: '11', count: 2,  pct: 33  },
    { grade: '12', count: 1,  pct: 17  },
  ],
  alerts: [
    { label: '1 records request on administrative hold',          severity: 'red'    },
    { label: '3 enrollment holds pending financial clearance',    severity: 'yellow' },
    { label: 'Semester end transcript deadline  Mar 15',        severity: 'yellow' },
  ],
};

async function fetchRegistrarMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/registrar/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_MAP = { complete: 'green', in_progress: 'blue', pending: 'yellow', hold: 'red' };

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

/*  Registrar KPI flip cards  */
const ADMIN_KPI = [
  { label: "Records Pending",    value: "8",    trend: null,             trendUp: null,
    definition: "Student records with incomplete or missing required fields awaiting review.",
    dataSource: "Registrar Module", dataHref: "/registrar" },
  { label: "Transcripts Issued", value: "14",   trend: null,             trendUp: null,
    definition: "Official transcripts issued to students, colleges, or third parties this month.",
    dataSource: "Registrar Module", dataHref: "/registrar" },
  { label: "Enrollment Count",   value: "742",  trend: null,             trendUp: null,
    definition: "Total verified active enrollment count for the current term.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "GPA Calc Status",    value: "Current", trend: null,          trendUp: null,
    definition: "Indicates whether the cumulative GPA calculation has been run for the current term.",
    dataSource: "Gradebook", dataHref: "/gradebook" },
];
export default function RegistrarDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchRegistrarMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const pendingList  = data.pending_requests_list    || DEMO.pending_requests_list;
  const txQueue      = data.transcript_queue         || DEMO.transcript_queue;
  const gradeEnroll  = data.new_enrollments_by_grade || DEMO.new_enrollments_by_grade;
  const alerts       = data.alerts                   || DEMO.alerts;

  return (
    <CrownLayout
      title="Registrar / Records"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Total Enrollment"   value={data.enrollment_total       ?? DEMO.enrollment_total}       /></Col>
          <Col span={3}><CrownMetricCard label="Pending Requests"   value={data.pending_requests       ?? DEMO.pending_requests}       /></Col>
          <Col span={3}><CrownMetricCard label="Transcripts (MTD)" value={data.transcripts_issued_mtd ?? DEMO.transcripts_issued_mtd} /></Col>
          <Col span={3}><CrownMetricCard label="Holds Active"       value={data.holds_active           ?? DEMO.holds_active}           /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Records Requests & Transcripts">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Pending Records Requests">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Request Type', 'Submitted', 'Target Date', 'Status'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {pendingList.map((r, i) => (
                    <tr key={i}>
                      <td style={TD}>{r.type}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{r.submitted}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{r.target_date}</td>
                      <td style={TD}><Pill color={STATUS_MAP[r.status] || 'gray'}>{r.status.replace('_', ' ')}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Transcript Queue">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Type', 'Count', 'Avg Days'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {txQueue.map((q, i) => (
                    <tr key={i}>
                      <td style={TD}>{q.destination_type}</td>
                      <td style={{ ...TD, fontWeight: 700 }}>{q.count}</td>
                      <td style={TD}>{q.avg_days}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="New Enrollments & Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="New Enrollments This Month by Grade">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {gradeEnroll.map((g, i) => (
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
