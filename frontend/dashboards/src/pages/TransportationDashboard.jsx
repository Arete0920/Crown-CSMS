import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection   from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

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

const DEMO = {
  routes_today:        8,
  riders_today:       214,
  late_runs:           1,
  maintenance_flags:   2,
  route_status: [
    { route: 'Route 1 — Northside',   driver: 'R. Davis',   status: 'on_time', riders: 28 },
    { route: 'Route 2 — Eastview',    driver: 'T. Johnson',  status: 'on_time', riders: 31 },
    { route: 'Route 3 — Southgate',   driver: 'M. Lee',     status: 'late',    riders: 25 },
    { route: 'Route 4 — Westpark',    driver: 'A. Martinez', status: 'on_time', riders: 27 },
    { route: 'Route 5 — Central',     driver: 'S. Clark',   status: 'on_time', riders: 22 },
    { route: 'Route 6 — Hillcrest',   driver: 'B. Walker',  status: 'on_time', riders: 26 },
    { route: 'Route 7 — Valley Rd',   driver: 'C. Hall',    status: 'on_time', riders: 29 },
    { route: 'Route 8 — Sports/AM',   driver: 'D. Young',   status: 'on_time', riders: 26 },
  ],
  driver_coverage: [
    { driver: 'R. Davis',    routes: 1, status: 'active' },
    { driver: 'T. Johnson',  routes: 1, status: 'active' },
    { driver: 'M. Lee',      routes: 1, status: 'active' },
    { driver: 'A. Martinez', routes: 1, status: 'active' },
    { driver: 'S. Clark',    routes: 1, status: 'active' },
    { driver: 'B. Walker',   routes: 1, status: 'active' },
    { driver: 'C. Hall',     routes: 1, status: 'active' },
    { driver: 'D. Young',    routes: 1, status: 'active' },
  ],
  incidents: [
    { date: 'Feb 20', route: 'Route 3', description: 'Minor delay — traffic accident on Oak Ave', resolved: true },
    { date: 'Feb 18', route: 'Route 5', description: 'Bus #14 fuel sensor warning — resolved at depot', resolved: true },
  ],
  alerts: [
    { label: 'Route 3 running 12 min late — parents notified',        severity: 'yellow' },
    { label: 'Bus #11 — oil change overdue (2,200 mi past schedule)', severity: 'red'    },
    { label: 'Bus #7 — tire inspection due this week',                 severity: 'yellow' },
    { label: 'Substitute driver needed for Route 2 on Feb 27',        severity: 'gray'   },
  ],
};

async function fetchTransportationMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/transportation/metrics/`;
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

const STATUS_COLOR = { on_time: 'green', late: 'red', cancelled: 'red' };

/* â”€â”€ Transportation KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Routes Active",     value: "8",    trend: null,              trendUp: null,
    definition: "Bus and carpool routes currently in operation for morning and afternoon runs.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "Students on Bus",   value: "142",  trend: null,              trendUp: null,
    definition: "Total students registered on daily bus routes (AM + PM).",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "On-Time Rate",      value: "97%",  trend: "+1% vs last wk",  trendUp: true,
    definition: "Percentage of route arrivals within 5 minutes of scheduled pickup/drop-off.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
  { label: "Incidents MTD",     value: "1",    trend: null,              trendUp: null,
    definition: "Transportation incidents (late, breakdown, safety issue) reported this month.",
    dataSource: "Transportation Module", dataHref: "/transportation" },
];
export default function TransportationDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchTransportationMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts    = data.alerts          || DEMO.alerts;
  const routes    = data.route_status    || DEMO.route_status;
  const drivers   = data.driver_coverage || DEMO.driver_coverage;
  const incidents = data.incidents       || DEMO.incidents;

  return (
    <CrownLayout
      title="Transportation"
      subtitle="Route status, driver coverage, riders, and maintenance tracking"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Routes Today" value={data.routes_today ?? DEMO.routes_today} /></Col>
          <Col span={3}><CrownMetricCard label="Riders Today" value={data.riders_today ?? DEMO.riders_today} /></Col>
          <Col span={3}><CrownMetricCard label="Late Runs" value={data.late_runs ?? DEMO.late_runs} /></Col>
          <Col span={3}><CrownMetricCard label="Maintenance Flags" value={data.maintenance_flags ?? DEMO.maintenance_flags} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Routes &amp; Incidents">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Route Status">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Route', 'Driver', 'Riders', 'Status'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {routes.map((r, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{r.route}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{r.driver}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)' }}>{r.riders}</td>
                      <td style={{ padding: '6px 8px' }}><Pill color={STATUS_COLOR[r.status] || 'gray'}>{r.status.replace('_', ' ')}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Recent Incidents">
              {incidents.length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--crown-ok)' }}>No incidents this week ✓</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {incidents.map((inc, i) => (
                    <div key={i} style={{ padding: '8px 10px', borderRadius: 5, background: 'var(--crown-surface-2)', border: '1px solid var(--crown-border)', fontSize: 13 }}>
                      <div style={{ fontWeight: 600, color: 'var(--crown-ink)' }}>{inc.route} — {inc.date}</div>
                      <div style={{ color: 'var(--crown-muted)', marginTop: 2 }}>{inc.description}</div>
                      {inc.resolved && <div style={{ color: 'var(--crown-ok)', fontSize: 11, marginTop: 4 }}>✓ Resolved</div>}
                    </div>
                  ))}
                </div>
              )}
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Alerts">
        <CrownGrid>
          <Col span={12}>
            <CrownCard title="Alerts &amp; Maintenance">
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
