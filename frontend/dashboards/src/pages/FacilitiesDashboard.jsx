import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

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
  work_orders_open:   12,
  sla_breaches:        2,
  inspections_due:     3,
  vendor_visits_this_week: 4,
  open_work_orders: [
    { id: 'WO-2201', location: 'Gym — HVAC',        description: 'Cooling unit failure', priority: 'high',   days_open: 3, assigned: 'M. Torres' },
    { id: 'WO-2198', location: 'Library',            description: 'Ceiling tile leak',   priority: 'high',   days_open: 5, assigned: 'J. Reyes'  },
    { id: 'WO-2195', location: 'Cafeteria kitchen',  description: 'Hood vent cleaning',  priority: 'normal', days_open: 8, assigned: 'M. Torres' },
    { id: 'WO-2193', location: 'Admin — B Wing',     description: 'LED retrofit',        priority: 'low',    days_open: 12, assigned: 'J. Reyes' },
    { id: 'WO-2190', location: 'Parking lot',        description: 'Line repainting',     priority: 'low',    days_open: 14, assigned: 'TBD'      },
  ],
  pm_calendar: [
    { task: 'Fire extinguisher inspection',   due: 'Feb 28', status: 'scheduled' },
    { task: 'Emergency lighting test',        due: 'Feb 28', status: 'scheduled' },
    { task: 'Roof inspection (spring)',       due: 'Mar 15', status: 'planned'   },
    { task: 'HVAC filter replacement — all', due: 'Mar 20', status: 'planned'   },
    { task: 'Elevator annual certification', due: 'Apr 1',  status: 'planned'   },
  ],
  top_categories: [
    { category: 'HVAC / Mechanical', count: 4 },
    { category: 'Plumbing',          count: 3 },
    { category: 'Electrical',        count: 2 },
    { category: 'General Repairs',   count: 2 },
    { category: 'Grounds',           count: 1 },
  ],
  alerts: [
    { label: 'WO-2198 — Library ceiling leak: SLA breach, day 5 (SLA = 3 days)', severity: 'red'    },
    { label: 'WO-2201 — Gym HVAC: SLA breach, cooling affecting PE classes',      severity: 'red'    },
    { label: '3 preventative maintenance inspections due before March 1',         severity: 'yellow' },
    { label: 'Elevator inspection 40 days out — schedule vendor',                 severity: 'gray'   },
  ],
};

async function fetchFacilitiesMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/facilities/metrics/`;
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

const PRIORITY_COLOR = { high: 'red', normal: 'yellow', low: 'gray' };
const PM_COLOR = { scheduled: 'yellow', planned: 'gray', completed: 'green' };

export default function FacilitiesDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchFacilitiesMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts     = data.alerts             || DEMO.alerts;
  const orders     = data.open_work_orders   || DEMO.open_work_orders;
  const pmCal      = data.pm_calendar        || DEMO.pm_calendar;
  const categories = data.top_categories     || DEMO.top_categories;
  const maxCat     = Math.max(...categories.map(c => c.count), 1);

  return (
    <CrownLayout
      title="Facilities"
      subtitle="Work orders, preventative maintenance, inspections, and vendor scheduling"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Open Work Orders"        value={data.work_orders_open         ?? DEMO.work_orders_open} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="SLA Breaches"            value={data.sla_breaches             ?? DEMO.sla_breaches} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Inspections Due"         value={data.inspections_due          ?? DEMO.inspections_due} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Vendor Visits (Week)"    value={data.vendor_visits_this_week  ?? DEMO.vendor_visits_this_week} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Open Work Orders ── */}
        <Col span={8}>
          <CrownCard title="Open Work Orders">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['ID', 'Location', 'Issue', 'Days Open', 'Assigned', 'Priority'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {orders.map((o, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', color: '#6366f1', fontWeight: 600 }}>{o.id}</td>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{o.location}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{o.description}</td>
                    <td style={{ padding: '6px 8px', color: o.days_open >= 5 ? '#dc2626' : '#374151', fontWeight: o.days_open >= 5 ? 700 : 400 }}>{o.days_open}d</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{o.assigned}</td>
                    <td style={{ padding: '6px 8px' }}><Pill color={PRIORITY_COLOR[o.priority] || 'gray'}>{o.priority}</Pill></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Top Categories ── */}
        <Col span={4}>
          <CrownCard title="Top Issue Categories">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {categories.map((c, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                    <span style={{ fontWeight: 500 }}>{c.category}</span>
                    <span style={{ color: '#6b7280' }}>{c.count}</span>
                  </div>
                  <div style={{ height: 6, background: '#e5e7eb', borderRadius: 4 }}>
                    <div style={{ height: 6, borderRadius: 4, width: `${Math.round((c.count / maxCat) * 100)}%`, background: '#f59e0b' }} />
                  </div>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── PM Calendar ── */}
        <Col span={6}>
          <CrownCard title="Preventative Maintenance Calendar">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {pmCal.map((p, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{p.task}</span>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ fontSize: 11, color: '#6b7280' }}>{p.due}</span>
                    <Pill color={PM_COLOR[p.status] || 'gray'}>{p.status}</Pill>
                  </div>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={6}>
          <CrownCard title="Alerts &amp; Overdue Items">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {alerts.map((a, i) => (
                <div key={i} style={{
                  padding: '8px 12px', borderRadius: 6,
                  background: a.severity === 'red' ? '#fee2e2' : a.severity === 'yellow' ? '#fef9c3' : '#f3f4f6',
                  border: `1px solid ${a.severity === 'red' ? '#fca5a5' : a.severity === 'yellow' ? '#fde047' : '#e5e7eb'}`,
                }}>
                  <span style={{ fontSize: 13, color: a.severity === 'red' ? '#991b1b' : a.severity === 'yellow' ? '#854d0e' : '#374151' }}>
                    {a.label}
                  </span>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
