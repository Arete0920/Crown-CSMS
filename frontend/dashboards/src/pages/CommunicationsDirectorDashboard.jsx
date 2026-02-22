import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
// NOTE: This dashboard lives at /communications-director to avoid conflicting
// with the existing /communications comms-inbox route (CommunicationsThreadsList).
// Token: communications_director → /communications-director

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
  messages_sent_week: 1840, open_rate_pct: 64, announcements_scheduled: 5, unsubscribes_week: 3,
  campaigns: [], channel_engagement: [], upcoming_announcements: [], alerts: [], snapshot_date: '—',
};

async function fetchCommunicationsMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/communications/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_COLOR = { sent: '#16a34a', scheduled: '#2563eb', draft: '#6b7280', failed: '#dc2626' };

function Pill({ v }) {
  const bg = STATUS_COLOR[v] || '#6b7280';
  return (
    <span style={{ background: bg, color: '#fff', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>
      {v}
    </span>
  );
}

export default function CommunicationsDirectorDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchCommunicationsMetrics().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;
  return (
    <CrownLayout title="Communications Director" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}>
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}
      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Messages Sent (Week)"      value={data.messages_sent_week}        />
        <CrownMetricCard label="Open Rate"                 value={`${data.open_rate_pct}%`}       />
        <CrownMetricCard label="Announcements Scheduled"   value={data.announcements_scheduled}   />
        <CrownMetricCard label="Unsubscribes (Week)"       value={data.unsubscribes_week}         />
      </div>

      {/* Recent Campaigns */}
      <CrownCard title="Recent Campaigns">
        <table className="crown-table">
          <thead><tr><th>Campaign</th><th>Sent</th><th>Open Rate</th><th>Status</th></tr></thead>
          <tbody>
            {(data.campaigns || []).map((c, i) => (
              <tr key={i}>
                <td>{c.name}</td>
                <td>{c.sent}</td>
                <td>{c.open_rate}</td>
                <td><Pill v={c.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CrownCard>

      {/* Channel Engagement */}
      <CrownCard title="Channel Engagement (MTD)">
        {(data.channel_engagement || []).map((ch, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
              <span>{ch.channel}</span><span style={{ fontWeight: 700 }}>{ch.open_rate}</span>
            </div>
            <div style={{ background: '#e5e7eb', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#0891b2', borderRadius: 4, height: 8, width: `${Math.min(ch.pct, 100)}%` }} />
            </div>
          </div>
        ))}
      </CrownCard>

      {/* Upcoming Announcements */}
      <CrownCard title="Upcoming Announcements">
        <table className="crown-table">
          <thead><tr><th>Subject</th><th>Audience</th><th>Scheduled</th><th>Status</th></tr></thead>
          <tbody>
            {(data.upcoming_announcements || []).map((a, i) => (
              <tr key={i}>
                <td>{a.subject}</td>
                <td>{a.audience}</td>
                <td>{a.scheduled}</td>
                <td><Pill v={a.status} /></td>
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
