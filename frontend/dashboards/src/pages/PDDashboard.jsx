import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
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
  sessions_this_month: 6, staff_hours_logged: 142, certifications_expiring: 4, satisfaction_avg: 4.3,
  upcoming_sessions: [], certifications: [], completion_by_dept: [], alerts: [], snapshot_date: '—',
};

async function fetchPDMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/pd/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_COLOR = { completed: '#16a34a', upcoming: '#2563eb', cancelled: '#dc2626', 'in progress': '#ca8a04' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v}
    </span>
  );
}

export default function PDDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchPDMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="PD / Staff Development" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Sessions This Month"        value={data.sessions_this_month}         />
        <CrownMetricCard label="Staff Hours Logged"         value={data.staff_hours_logged}          />
        <CrownMetricCard label="Certifications Expiring"    value={data.certifications_expiring}     />
        <CrownMetricCard label="Avg Satisfaction Score"     value={`${data.satisfaction_avg}/5`}     />
      </div>

      {/* Upcoming Sessions */}
      <CrownCard title="Upcoming Sessions">
        <table className="crown-table">
          <thead><tr><th>Session</th><th>Date</th><th>Facilitator</th><th>Registered</th><th>Status</th></tr></thead>
          <tbody>
            {(data.upcoming_sessions || []).map((s, i) => (
              <tr key={i}>
                <td>{s.title}</td>
                <td>{s.date}</td>
                <td>{s.facilitator}</td>
                <td>{s.registered}</td>
                <td><Pill v={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Certification Tracker */}
      <CrownCard title="Certification Tracker">
        <table className="crown-table">
          <thead><tr><th>Certification</th><th>Staff Count</th><th>Expiring (90d)</th></tr></thead>
          <tbody>
            {(data.certifications || []).map((c, i) => (
              <tr key={i}>
                <td>{c.name}</td>
                <td>{c.staff_count}</td>
                <td style={{ color: c.expiring_90d > 0 ? '#dc2626' : 'inherit', fontWeight: c.expiring_90d > 0 ? 700 : 400 }}>
                  {c.expiring_90d}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Staff Completion by Department */}
      <CrownCard title="Staff Completion by Department">
        {(data.completion_by_dept || []).map((d, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{d.dept}</span><span style={{ fontWeight: 700 }}>{d.pct}%</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: d.pct >= 80 ? '#16a34a' : '#ca8a04', borderRadius: 4, height: 8, width: `${Math.min(d.pct, 100)}%` }} />
            </div>
          </div>
        ))}
      </CrownCard>

      {/* Alerts */}
      <CrownCard title="Alerts">
        {(data.alerts || []).map((a, i) => (
          <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #f3f4f6', display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: a.severity === 'red' ? '#dc2626' : a.severity === 'yellow' ? '#ca8a04' : '#9ca3af', flexShrink: 0 }} />
            <span style={{ fontSize: 13 }}>{a.label}</span>
          </div>
        ))}
      </CrownCard>
    </CrownLayout>
  );
}
