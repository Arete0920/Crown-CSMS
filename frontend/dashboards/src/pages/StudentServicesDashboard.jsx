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
  lunch_balance_alerts: 31, unpaid_balances_total: 1140, applications_pending: 7, services_active: 89,
  balance_alerts_by_grade: [], services_by_type: [], pending_applications: [], alerts: [], snapshot_date: '—',
};

async function fetchStudentServicesMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/student-services/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const SEV_COLOR = { critical: '#dc2626', warning: '#ca8a04', info: '#2563eb' };

function Pill({ v }) {
  const bg = SEV_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v}
    </span>
  );
}

export default function StudentServicesDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchStudentServicesMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Student Services" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Lunch Balance Alerts"    value={data.lunch_balance_alerts}    />
        <CrownMetricCard label="Unpaid Balances"         value={`$${data.unpaid_balances_total}`} />
        <CrownMetricCard label="Applications Pending"    value={data.applications_pending}    />
        <CrownMetricCard label="Active Services"         value={data.services_active}         />
      </div>

      {/* Balance Alerts — aggregate, no names */}
      <CrownCard title="Balance Alert Summary (Aggregate)">
        <table className="crown-table">
          <thead><tr><th>Grade</th><th>Accounts Below $5</th><th>Accounts at $0</th><th>Severity</th></tr></thead>
          <tbody>
            {(data.balance_alerts_by_grade || []).map((g, i) => (
              <tr key={i}>
                <td>Grade {g.grade}</td>
                <td>{g.below_five}</td>
                <td>{g.at_zero}</td>
                <td><Pill v={g.severity} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Active Services */}
      <CrownCard title="Active Services by Type">
        {(data.services_by_type || []).map((s, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{s.type}</span><span style={{ fontWeight: 700 }}>{s.count} students</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#7c3aed', borderRadius: 4, height: 8, width: `${Math.min(s.pct, 100)}%` }} />
            </div>
          </div>
        ))}
      </CrownCard>

      {/* Pending Applications */}
      <CrownCard title="Pending Applications">
        <table className="crown-table">
          <thead><tr><th>Service Type</th><th>Count</th><th>Oldest (days)</th></tr></thead>
          <tbody>
            {(data.pending_applications || []).map((a, i) => (
              <tr key={i}>
                <td>{a.service_type}</td>
                <td>{a.count}</td>
                <td style={{ color: a.oldest_days >= 10 ? '#dc2626' : 'inherit', fontWeight: a.oldest_days >= 10 ? 700 : 400 }}>
                  {a.oldest_days}d
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
