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
  drills_completed_ytd:    4,
  incidents_week:          1,
  door_access_exceptions:  3,
  camera_uptime_pct:      98,
  incident_log: [
    { date: 'Feb 21', type: 'Unauthorized entry attempt', location: 'South entrance', severity: 'medium', status: 'resolved' },
    { date: 'Feb 14', type: 'After-hours access',         location: 'Gym side door',  severity: 'low',    status: 'resolved' },
    { date: 'Jan 30', type: 'Visitor badge violation',    location: 'Admin lobby',    severity: 'low',    status: 'resolved' },
  ],
  drill_schedule: [
    { drill: 'Fire Drill',          date: 'Mar 5',  status: 'scheduled', required: true },
    { drill: 'Lockdown (ALICE)',     date: 'Mar 19', status: 'scheduled', required: true },
    { drill: 'Shelter-in-Place',    date: 'Apr 9',  status: 'planned',   required: true },
    { drill: 'Evacuation (full)',    date: 'Apr 23', status: 'planned',   required: true },
  ],
  open_issues: [
    { issue: 'Camera #7 — Main Hall (west): offline 2 days', severity: 'red'    },
    { issue: 'Fob access log: 2 unknown badge scans Feb 22', severity: 'yellow' },
    { issue: 'South gate key pad battery low',               severity: 'yellow' },
  ],
  alerts: [
    { label: 'Camera #7 offline — main hall west blind spot until repaired',     severity: 'red'    },
    { label: '3 door access exceptions logged — review required',                severity: 'yellow' },
    { label: 'Next required drill due Mar 5 — logistics not yet confirmed',      severity: 'yellow' },
    { label: 'Annual safety checklist review due March 31',                      severity: 'gray'   },
  ],
};

async function fetchSecurityMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/security/metrics/`;
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

const SEV_COLOR = { high: 'red', medium: 'yellow', low: 'gray' };
const DRILL_COLOR = { scheduled: 'yellow', planned: 'gray', completed: 'green' };

/* â”€â”€ Security KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Visitors Logged",   value: "14",        trend: null,            trendUp: null,
    definition: "Visitors signed in through the front-office visitor management system today.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Access Events",     value: "847",       trend: null,            trendUp: null,
    definition: "Total door access log events recorded today across all controlled entry points.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Camera Status",     value: "All Online",trend: null,            trendUp: null,
    definition: "Status of the campus security camera network — all feeds online and recording.",
    dataSource: "Security Module", dataHref: "/security" },
  { label: "Incidents MTD",     value: "1",         trend: "-1 vs last mo", trendUp: true,
    definition: "Security incidents (unauthorized access, alarm triggers) logged this month.",
    dataSource: "Security Module", dataHref: "/security" },
];
export default function SecurityDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchSecurityMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts     = data.alerts         || DEMO.alerts;
  const incidents  = data.incident_log   || DEMO.incident_log;
  const drills     = data.drill_schedule || DEMO.drill_schedule;
  const openIssues = data.open_issues    || DEMO.open_issues;

  return (
    <CrownLayout
      title="Security &amp; Safety"
      subtitle="Drills, incidents, access control, and camera monitoring"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Drills Completed (YTD)" value={data.drills_completed_ytd ?? DEMO.drills_completed_ytd} /></Col>
          <Col span={3}><CrownMetricCard label="Incidents (This Week)" value={data.incidents_week ?? DEMO.incidents_week} /></Col>
          <Col span={3}><CrownMetricCard label="Door Access Exceptions" value={data.door_access_exceptions ?? DEMO.door_access_exceptions} /></Col>
          <Col span={3}><CrownMetricCard label="Camera Uptime %" value={`${data.camera_uptime_pct ?? DEMO.camera_uptime_pct}%`} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Incidents &amp; Drills">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Incident Log (Redacted)">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Date', 'Type', 'Location', 'Severity', 'Status'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((inc, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)', whiteSpace: 'nowrap' }}>{inc.date}</td>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{inc.type}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{inc.location}</td>
                      <td style={{ padding: '6px 8px' }}><Pill color={SEV_COLOR[inc.severity] || 'gray'}>{inc.severity}</Pill></td>
                      <td style={{ padding: '6px 8px' }}><Pill color={inc.status === 'resolved' ? 'green' : 'yellow'}>{inc.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Drill Schedule">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {drills.map((d, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--crown-border)' }}>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 13, color: 'var(--crown-ink)' }}>{d.drill}</div>
                      <div style={{ fontSize: 11, color: 'var(--crown-muted)' }}>{d.date}</div>
                    </div>
                    <Pill color={DRILL_COLOR[d.status] || 'gray'}>{d.status}</Pill>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Issues &amp; Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Open Issues">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {openIssues.map((issue, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: issue.severity === 'red' ? 'var(--crown-danger-bg)' : issue.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: issue.severity === 'red' ? 'var(--crown-danger)' : issue.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{issue.issue}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts &amp; Safety Checklist">
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
