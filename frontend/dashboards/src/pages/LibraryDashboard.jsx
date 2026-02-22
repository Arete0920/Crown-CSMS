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
  books_checked_out: 248, overdue_items: 17, new_materials_this_month: 34, digital_resources_active: 6,
  overdue_list: [], collection_by_category: [], digital_resources: [], alerts: [], snapshot_date: '—',
};

async function fetchLibraryMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/library/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

export default function LibraryDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchLibraryMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Library / Media Center" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
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
