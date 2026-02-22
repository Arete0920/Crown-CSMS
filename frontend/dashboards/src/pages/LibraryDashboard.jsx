import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchLibraryMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/library/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function LibraryDashboard() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLibraryMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="Library"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="Library"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="Library / Media Center" subtitle={`Snapshot: ${data.snapshot_date}`}>
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Books Checked Out"          value={data.books_checked_out}          />
        <CrownMetricCard label="Overdue Items"              value={data.overdue_items}               />
        <CrownMetricCard label="New Materials (This Month)" value={data.new_materials_this_month}    />
        <CrownMetricCard label="Digital Resources Active"  value={data.digital_resources_active}    />
      </div>

      {/* Overdue Items */}
      <CrownCard title="Overdue Items (Redacted — Staff View)">
        <table className="crown-table">
          <thead><tr><th>Borrower ID</th><th>Title</th><th>Due Date</th><th>Days Overdue</th></tr></thead>
          <tbody>
            {(data.overdue_list || []).map((item, i) => (
              <tr key={i}
                style={{ background: item.days_overdue >= 14 ? '#fef2f2' : 'transparent' }}>
                <td>{item.borrower_id}</td>
                <td>{item.title}</td>
                <td>{item.due_date}</td>
                <td style={{ color: item.days_overdue >= 14 ? '#dc2626' : 'inherit', fontWeight: item.days_overdue >= 14 ? 700 : 400 }}>
                  {item.days_overdue}d
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Collection Highlights */}
      <CrownCard title="Collection by Category">
        {(data.collection_by_category || []).map((c, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{c.category}</span><span style={{ fontWeight: 700 }}>{c.count} items</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#0891b2', borderRadius: 4, height: 8, width: `${Math.min(c.pct, 100)}%` }} />
            </div>
          </div>
        ))}
      </CrownCard>

      {/* Digital Resources */}
      <CrownCard title="Digital Resources">
        <table className="crown-table">
          <thead><tr><th>Resource</th><th>Active Licenses</th><th>Usage (MTD)</th></tr></thead>
          <tbody>
            {(data.digital_resources || []).map((r, i) => (
              <tr key={i}>
                <td>{r.name}</td>
                <td>{r.licenses}</td>
                <td>{r.usage_mtd}</td>
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
