import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchRegistrarMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/registrar/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const STATUS_COLOR = { complete: '#16a34a', pending: '#ca8a04', hold: '#dc2626', in_progress: '#2563eb' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v.replace('_', ' ')}
    </span>
  );
}

export default function RegistrarDashboard() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRegistrarMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="Registrar"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="Registrar"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="Registrar / Records" subtitle={`Snapshot: ${data.snapshot_date}`}>
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Total Enrollment"       value={data.enrollment_total}       />
        <CrownMetricCard label="Pending Requests"       value={data.pending_requests}       />
        <CrownMetricCard label="Transcripts (MTD)"      value={data.transcripts_issued_mtd} />
        <CrownMetricCard label="Holds Active"           value={data.holds_active}           />
      </div>

      {/* Pending Records Requests */}
      <CrownCard title="Pending Records Requests">
        <table className="crown-table">
          <thead><tr><th>Request Type</th><th>Submitted</th><th>Target Date</th><th>Status</th></tr></thead>
          <tbody>
            {(data.pending_requests_list || []).map((r, i) => (
              <tr key={i}>
                <td>{r.type}</td>
                <td>{r.submitted}</td>
                <td>{r.target_date}</td>
                <td><Pill v={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Transcript Queue */}
      <CrownCard title="Transcript Queue">
        <table className="crown-table">
          <thead><tr><th>Destination Type</th><th>Count</th><th>Avg Days</th></tr></thead>
          <tbody>
            {(data.transcript_queue || []).map((q, i) => (
              <tr key={i}>
                <td>{q.destination_type}</td>
                <td>{q.count}</td>
                <td>{q.avg_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* New Enrollments */}
      <CrownCard title="New Enrollments This Month">
        {(data.new_enrollments_by_grade || []).map((g, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>Grade {g.grade}</span><span style={{ fontWeight: 700 }}>{g.count}</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#2563eb', borderRadius: 4, height: 8, width: `${Math.min(g.pct, 100)}%` }} />
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
