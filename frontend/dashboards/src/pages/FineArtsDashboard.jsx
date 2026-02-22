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
  enrolled_students: 186, performances_this_term: 4, equipment_needs: 3, parent_volunteers: 22,
  performances: [], ensembles: [], equipment_list: [], alerts: [], snapshot_date: '—',
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

const STATUS_COLOR = { scheduled: '#16a34a', confirmed: '#2563eb', pending: '#ca8a04', cancelled: '#dc2626' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v}
    </span>
  );
}

export default function FineArtsDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchFineArtsMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Fine Arts" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Enrolled Students"         value={data.enrolled_students}        />
        <CrownMetricCard label="Performances This Term"    value={data.performances_this_term}   />
        <CrownMetricCard label="Equipment Needs Flagged"   value={data.equipment_needs}          />
        <CrownMetricCard label="Parent Volunteers Active"  value={data.parent_volunteers}        />
      </div>

      {/* Upcoming Performances */}
      <CrownCard title="Upcoming Performances">
        <table className="crown-table">
          <thead><tr><th>Event</th><th>Date</th><th>Venue</th><th>Status</th></tr></thead>
          <tbody>
            {(data.performances || []).map((p, i) => (
              <tr key={i}>
                <td>{p.event}</td>
                <td>{p.date}</td>
                <td>{p.venue}</td>
                <td><Pill v={p.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Ensemble Enrollment */}
      <CrownCard title="Ensemble Enrollment">
        {(data.ensembles || []).map((e, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{e.name}</span><span style={{ fontWeight: 700 }}>{e.students} students</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#7c3aed', borderRadius: 4, height: 8, width: `${Math.min(e.pct, 100)}%` }} />
            </div>
          </div>
        ))}
      </CrownCard>

      {/* Equipment Tracker */}
      <CrownCard title="Equipment Tracker">
        <table className="crown-table">
          <thead><tr><th>Item</th><th>Qty Needed</th><th>Est. Cost</th><th>Priority</th></tr></thead>
          <tbody>
            {(data.equipment_list || []).map((eq, i) => (
              <tr key={i}
                style={{ background: eq.priority === 'high' ? '#fef9c3' : 'transparent' }}>
                <td>{eq.item}</td>
                <td>{eq.qty}</td>
                <td>{eq.est_cost}</td>
                <td style={{ fontWeight: eq.priority === 'high' ? 700 : 400 }}>{eq.priority}</td>
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
