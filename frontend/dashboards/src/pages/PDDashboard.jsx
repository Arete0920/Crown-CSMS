import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchPDMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/pd/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPDMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="PD Hub"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="PD Hub"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="PD / Staff Development" subtitle={`Snapshot: ${data.snapshot_date}`}>
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
