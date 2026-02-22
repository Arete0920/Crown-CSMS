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
  enrolled_today: 74, staff_ratio: '1:8', incidents_week: 1, invoices_pending: 12,
  roster_summary: [], staff_schedule: [], weekly_trend: [], alerts: [], snapshot_date: '—',
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

const STATUS_COLOR = { present: '#16a34a', absent: '#dc2626', late_pickup: '#ca8a04' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v.replace('_', ' ')}
    </span>
  );
}

export default function ExtendedCareDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchExtendedCareMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Extended Care / Aftercare" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Enrolled Today"      value={data.enrolled_today}      />
        <CrownMetricCard label="Staff : Child Ratio" value={data.staff_ratio}         />
        <CrownMetricCard label="Incidents This Week" value={data.incidents_week}      />
        <CrownMetricCard label="Invoices Pending"    value={data.invoices_pending}    />
      </div>

      {/* Today's Roster — aggregate counts, no names */}
      <CrownCard title="Today's Program Roster (Aggregate)">
        <table className="crown-table">
          <thead><tr><th>Program</th><th>Enrolled</th><th>Present</th><th>Late Pickup</th></tr></thead>
          <tbody>
            {(data.roster_summary || []).map((r, i) => (
              <tr key={i}>
                <td>{r.program}</td>
                <td>{r.enrolled}</td>
                <td>{r.present}</td>
                <td style={{ color: r.late_pickup > 0 ? '#ca8a04' : 'inherit', fontWeight: r.late_pickup > 0 ? 700 : 400 }}>
                  {r.late_pickup}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Staff Schedule */}
      <CrownCard title="Staff Schedule Today">
        <table className="crown-table">
          <thead><tr><th>Staff</th><th>Shift</th><th>Program</th><th>Status</th></tr></thead>
          <tbody>
            {(data.staff_schedule || []).map((s, i) => (
              <tr key={i}>
                <td>{s.name}</td>
                <td>{s.shift}</td>
                <td>{s.program}</td>
                <td><Pill v={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Weekly Attendance Trend */}
      <CrownCard title="Weekly Attendance Trend">
        {(data.weekly_trend || []).map((d, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{d.day}</span><span style={{ fontWeight: 700 }}>{d.count} students</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#16a34a', borderRadius: 4, height: 8, width: `${Math.min(d.pct, 100)}%` }} />
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
