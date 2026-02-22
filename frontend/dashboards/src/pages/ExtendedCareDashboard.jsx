import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchExtendedCareMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/extended-care/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchExtendedCareMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="Extended Care"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="Extended Care"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="Extended Care / Aftercare" subtitle={`Snapshot: ${data.snapshot_date}`}>
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
