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
  students_on_iep: 47, upcoming_reviews: 9, accommodations_active: 112, referrals_pending: 4,
  iep_reviews: [], accommodations_by_grade: [], caseload: [], alerts: [], snapshot_date: '—',
};

async function fetchAcademicSupportMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/academic-support/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_COLOR = { active: '#16a34a', pending: '#ca8a04', closed: '#6b7280', flagged: '#dc2626' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v}
    </span>
  );
}

export default function AcademicSupportDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchAcademicSupportMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Academic Support / SPED" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Students on IEP"        value={data.students_on_iep}        />
        <CrownMetricCard label="Reviews Due (30 days)"  value={data.upcoming_reviews}        />
        <CrownMetricCard label="Active Accommodations"  value={data.accommodations_active}   />
        <CrownMetricCard label="Referrals Pending"      value={data.referrals_pending}       />
      </div>

      {/* IEP Review Calendar */}
      <CrownCard title="IEP Review Calendar">
        <table className="crown-table">
          <thead><tr><th>Student (redacted)</th><th>Type</th><th>Due Date</th><th>Status</th></tr></thead>
          <tbody>
            {(data.iep_reviews || []).map((r, i) => (
              <tr key={i}>
                <td>{r.student_id}</td>
                <td>{r.type}</td>
                <td>{r.due_date}</td>
                <td><Pill v={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Active Accommodations by Grade */}
      <CrownCard title="Active Accommodations by Grade">
        {(data.accommodations_by_grade || []).map((g, i) => (
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

      {/* Learning Support Caseload */}
      <CrownCard title="Learning Support Caseload">
        <table className="crown-table">
          <thead><tr><th>Specialist</th><th>Active Plans</th><th>Pending Reviews</th></tr></thead>
          <tbody>
            {(data.caseload || []).map((c, i) => (
              <tr key={i}>
                <td>{c.specialist}</td>
                <td>{c.active_plans}</td>
                <td style={{ color: c.pending_reviews > 3 ? '#dc2626' : 'inherit', fontWeight: c.pending_reviews > 3 ? 700 : 400 }}>
                  {c.pending_reviews}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Alerts — aggregate only, no student names */}
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
