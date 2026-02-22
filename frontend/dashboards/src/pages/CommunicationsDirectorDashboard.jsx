import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { getAccessToken } from '../utils/authClient.js';

// NOTE: This dashboard lives at /communications-director to avoid conflicting
// with the existing /communications comms-inbox route (CommunicationsThreadsList).
// Token: communications_director → /communications-director

const DEMO = { schoolId: '19801b59-8c05-4c84-9312-5d792e4e839d' };

async function fetchCommunicationsMetrics() {
  const token    = getAccessToken();
  const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('crown.school.id') || DEMO.schoolId;
  const res = await fetch('/api/v1/communications/metrics/', {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-School-Id': schoolId,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCommunicationsMetrics().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <CrownLayout title="Communications"><p style={{ color: 'red' }}>{error}</p></CrownLayout>;
  if (!data)  return <CrownLayout title="Communications"><p>Loading…</p></CrownLayout>;

  return (
    <CrownLayout title="Communications Director" subtitle={`Snapshot: ${data.snapshot_date}`}>
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
