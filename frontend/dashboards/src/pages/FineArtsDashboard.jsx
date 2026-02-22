import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchFineArtsMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/fine-arts/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFineArtsMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="Fine Arts"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="Fine Arts"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="Fine Arts" subtitle={`Snapshot: ${data.snapshot_date}`}>
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
