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
  enrollment_total: 412, pending_requests: 8, transcripts_issued_mtd: 23, holds_active: 3,
  pending_requests_list: [], transcript_queue: [], new_enrollments_by_grade: [], alerts: [], snapshot_date: '—',
};

async function fetchRegistrarMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/registrar/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
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
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchRegistrarMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Registrar / Records" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
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
