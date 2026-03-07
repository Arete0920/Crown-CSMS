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
  enrolled_students: 186, performances_this_term: 4, equipment_needs: 3, parent_volunteers: 22,
  snapshot_date: 'Feb 26, 2026',
  performances: [
    { event: 'Spring Choir Concert',     date: 'Mar 14', venue: 'Main Auditorium', status: 'confirmed'  },
    { event: 'Drama: Into the Woods',    date: 'Apr 2',  venue: 'Black Box',       status: 'scheduled' },
    { event: 'Orchestra Open Night',     date: 'Apr 18', venue: 'Main Auditorium', status: 'pending'   },
    { event: 'End-of-Year Gala',         date: 'May 20', venue: 'Main Auditorium', status: 'pending'   },
  ],
  ensembles: [
    { name: 'Concert Choir',     students: 54, pct: 88 },
    { name: 'Orchestra',         students: 42, pct: 72 },
    { name: 'Drama / Theatre',   students: 38, pct: 65 },
    { name: 'Guitar Ensemble',   students: 28, pct: 48 },
    { name: 'Jazz Band',         students: 24, pct: 40 },
  ],
  equipment_list: [
    { item: 'Music stands (×12)',      qty: 12, est_cost: '$480',  priority: 'medium' },
    { item: 'Drum kit – snare heads',  qty:  4, est_cost: '$280',  priority: 'high'   },
    { item: 'Stage lighting upgrade',  qty:  1, est_cost: '$2400', priority: 'high'   },
  ],
  alerts: [
    { label: '3 equipment needs flagged — budget approval pending', severity: 'yellow' },
    { label: 'Drama production liability forms due Mar 1',          severity: 'yellow' },
  ],
};

async function fetchFineArtsMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/fine-arts/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_MAP = { scheduled: 'blue', confirmed: 'green', pending: 'yellow', cancelled: 'red' };

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

/* â”€â”€ Fine Arts KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Ensembles Active",    value: "4",  trend: null,              trendUp: null,
    definition: "Active musical, theatre, or visual arts groups with current rosters.",
    dataSource: "Fine Arts Module", dataHref: "/fine-arts" },
  { label: "Students Enrolled",   value: "62", trend: null,              trendUp: null,
    definition: "Total students enrolled in at least one fine arts course or ensemble this term.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Performances This Yr",value: "3",  trend: null,              trendUp: null,
    definition: "Public performances or showcases completed this academic year.",
    dataSource: "Calendar Module", dataHref: "/calendar" },
  { label: "Auditions Upcoming",  value: "1",  trend: null,              trendUp: null,
    definition: "Scheduled auditions or tryouts for upcoming ensembles or productions.",
    dataSource: "Fine Arts Module", dataHref: "/fine-arts" },
];
export function FineArtsDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchFineArtsMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const performances  = data.performances  || DEMO.performances;
  const ensembles     = data.ensembles     || DEMO.ensembles;
  const equipmentList = data.equipment_list|| DEMO.equipment_list;
  const alerts        = data.alerts        || DEMO.alerts;

  return (
    <CrownLayout
      title="Fine Arts"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Enrolled Students"        value={data.enrolled_students      ?? DEMO.enrolled_students}      /></Col>
          <Col span={3}><CrownMetricCard label="Performances This Term"   value={data.performances_this_term ?? DEMO.performances_this_term} /></Col>
          <Col span={3}><CrownMetricCard label="Equipment Needs Flagged"  value={data.equipment_needs        ?? DEMO.equipment_needs}        /></Col>
          <Col span={3}><CrownMetricCard label="Parent Volunteers Active" value={data.parent_volunteers      ?? DEMO.parent_volunteers}      /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Performances & Ensembles">
        <CrownGrid>
          <Col span={7}>
            <CrownCard title="Upcoming Performances">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Event', 'Date', 'Venue', 'Status'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {performances.map((p, i) => (
                    <tr key={i}>
                      <td style={TD}>{p.event}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{p.date}</td>
                      <td style={TD}>{p.venue}</td>
                      <td style={TD}><Pill color={STATUS_MAP[p.status] || 'gray'}>{p.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={5}>
            <CrownCard title="Ensemble Enrollment">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {ensembles.map((e, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)' }}>{e.name}</span>
                      <span style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{e.students}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.min(e.pct, 100)}%`, height: '100%', background: 'var(--crown-accent)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Equipment & Alerts">
        <CrownGrid>
          <Col span={7}>
            <CrownCard title="Equipment Tracker">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Item', 'Qty', 'Est. Cost', 'Priority'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {equipmentList.map((eq, i) => (
                    <tr key={i} style={{ background: eq.priority === 'high' ? 'var(--crown-warn-bg)' : '' }}>
                      <td style={TD}>{eq.item}</td>
                      <td style={TD}>{eq.qty}</td>
                      <td style={TD}>{eq.est_cost}</td>
                      <td style={{ ...TD, fontWeight: eq.priority === 'high' ? 700 : 400,
                        color: eq.priority === 'high' ? 'var(--crown-warn)' : 'var(--crown-muted)' }}>{eq.priority}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={5}>
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
export default FineArtsDashboard;