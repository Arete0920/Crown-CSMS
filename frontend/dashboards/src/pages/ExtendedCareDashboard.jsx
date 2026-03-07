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
  enrolled_today: 74, staff_ratio: '1:8', incidents_week: 1, invoices_pending: 12,
  snapshot_date: 'Feb 26, 2026',
  roster_summary: [
    { program: 'Before Care (7–8 AM)',  enrolled: 28, present: 27, late_pickup: 0 },
    { program: 'After Care (3–5 PM)',   enrolled: 38, present: 37, late_pickup: 2 },
    { program: 'After Care (5–6 PM)',   enrolled: 18, present: 17, late_pickup: 1 },
  ],
  staff_schedule: [
    { name: 'L. Carter',   shift: '6:45–8:15 AM', program: 'Before Care', status: 'present' },
    { name: 'M. Okonkwo', shift: '2:45–5:00 PM', program: 'After Care',  status: 'present' },
    { name: 'T. Rivera',  shift: '2:45–6:00 PM', program: 'After Care',  status: 'present' },
    { name: 'J. Smith',   shift: '4:00–6:00 PM', program: 'After Care',  status: 'absent'  },
  ],
  weekly_trend: [
    { day: 'Mon', count: 69, pct: 93 },
    { day: 'Tue', count: 72, pct: 97 },
    { day: 'Wed', count: 74, pct: 100 },
    { day: 'Thu', count: 67, pct: 90 },
    { day: 'Fri', count: 62, pct: 84 },
  ],
  alerts: [
    { label: '3 late pickups this week — 2 past the 6 PM cutoff', severity: 'yellow' },
    { label: '1 staff absent afternoon — ratio at boundary',       severity: 'yellow' },
    { label: '12 invoices pending payment or approval',            severity: 'red'    },
  ],
};

async function fetchExtendedCareMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/extended-care/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_MAP = { present: 'green', absent: 'red', late_pickup: 'yellow' };

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

const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

/* â”€â”€ Extended Care KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Enrolled Today",    value: "47",    trend: null,             trendUp: null,
    definition: "Students registered for extended care (before/aftercare) today.",
    dataSource: "Extended Care Module", dataHref: "/extended-care" },
  { label: "Checked In",        value: "43",    trend: null,             trendUp: null,
    definition: "Students who have been checked in by staff today.",
    dataSource: "Extended Care Module", dataHref: "/extended-care" },
  { label: "Revenue Today",     value: "$705",  trend: null,             trendUp: null,
    definition: "Fees collected today for extended care services (hourly + flat-rate).",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff On Duty",     value: "5",     trend: null,             trendUp: null,
    definition: "Extended care staff members currently clocked in and on duty.",
    dataSource: "HR Module", dataHref: "/human-resources" },
];
export default function ExtendedCareDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchExtendedCareMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const roster     = data.roster_summary || DEMO.roster_summary;
  const staff      = data.staff_schedule || DEMO.staff_schedule;
  const trend      = data.weekly_trend   || DEMO.weekly_trend;
  const alerts     = data.alerts         || DEMO.alerts;

  return (
    <CrownLayout
      title="Extended Care / Aftercare"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Enrolled Today"      value={data.enrolled_today  ?? DEMO.enrolled_today}  /></Col>
          <Col span={3}><CrownMetricCard label="Staff : Child Ratio" value={data.staff_ratio      ?? DEMO.staff_ratio}      /></Col>
          <Col span={3}><CrownMetricCard label="Incidents This Week" value={data.incidents_week   ?? DEMO.incidents_week}   /></Col>
          <Col span={3}><CrownMetricCard label="Invoices Pending"    value={data.invoices_pending ?? DEMO.invoices_pending} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Today's Roster & Staff">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Today's Program Roster">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Program', 'Enrolled', 'Present', 'Late Pickup'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {roster.map((r, i) => (
                    <tr key={i}>
                      <td style={TD}>{r.program}</td>
                      <td style={TD}>{r.enrolled}</td>
                      <td style={{ ...TD, color: 'var(--crown-ok)', fontWeight: 700 }}>{r.present}</td>
                      <td style={{ ...TD, color: r.late_pickup > 0 ? 'var(--crown-warn)' : 'var(--crown-muted)', fontWeight: r.late_pickup > 0 ? 700 : 400 }}>{r.late_pickup}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Staff Schedule Today">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Staff', 'Shift', 'Program', 'Status'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {staff.map((s, i) => (
                    <tr key={i}>
                      <td style={TD}>{s.name}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{s.shift}</td>
                      <td style={TD}>{s.program}</td>
                      <td style={TD}><Pill color={STATUS_MAP[s.status] || 'gray'}>{s.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Weekly Trend & Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Weekly Attendance Trend">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {trend.map((d, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)', fontWeight: 600 }}>{d.day}</span>
                      <span style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{d.count} students</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.min(d.pct, 100)}%`, height: '100%', background: 'var(--crown-ok)', borderRadius: 4 }} />
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
