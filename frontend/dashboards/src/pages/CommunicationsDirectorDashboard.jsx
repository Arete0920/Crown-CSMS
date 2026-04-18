import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
// NOTE: This dashboard lives at /communications-director to avoid conflicting
// with the existing /communications comms-inbox route (CommunicationsThreadsList).
// Token: communications_director  /communications-director

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
  snapshot_date: '2026-02-28',
  campaigns: [
    { name: 'Spring Enrollment Drive',  sent: 1240, open_rate: '68%', status: 'sent'      },
    { name: 'Family Night Invite',       sent:  430, open_rate: '71%', status: 'sent'      },
    { name: 'Tuition Reminder Q2',       sent:    0, open_rate: '',   status: 'scheduled' },
    { name: 'Summer Program Preview',    sent:    0, open_rate: '',   status: 'draft'     },
  ],
  channel_engagement: [
    { channel: 'Email',       open_rate: '68%', pct: 68 },
    { channel: 'Push (App)',  open_rate: '52%', pct: 52 },
    { channel: 'SMS',         open_rate: '84%', pct: 84 },
  ],
  upcoming_announcements: [
    { subject: 'Spring Field Day Details',  audience: 'All Families',  scheduled: '2026-03-05', status: 'scheduled' },
    { subject: 'Tuition Portal Open  Q2',  audience: 'All Families',  scheduled: '2026-03-10', status: 'scheduled' },
    { subject: 'Board Meeting Summary',     audience: 'Staff',         scheduled: '2026-03-12', status: 'draft'     },
  ],
  alerts: [
    { label: '3 unsubscribes this week  review list hygiene', severity: 'yellow' },
    { label: 'SMS delivery rate dropped to 91% (was 97%)',       severity: 'red'    },
  ],
};

async function fetchCommunicationsMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/communications/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

const STATUS_PILL = { sent: 'green', scheduled: 'blue', draft: 'gray', failed: 'red' };

function Pill({ color = 'gray', children }) {
  const map = {
    red:    { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)'  },
    yellow: { bg: 'var(--crown-warn-bg)',   fg: 'var(--crown-warn)'    },
    green:  { bg: 'var(--crown-ok-bg)',     fg: 'var(--crown-ok)'      },
    blue:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-brand)'   },
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

/*  Communications KPI flip cards  */
const ADMIN_KPI = [
  { label: "Messages Today",     value: "14",  trend: null,              trendUp: null,
    definition: "Total messages sent through the Crown platform today (email, SMS, in-app).",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Open Rate",          value: "68%", trend: "+4% vs last wk",  trendUp: true,
    definition: "Percentage of messages sent today that were opened by at least one recipient.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Active Threads",     value: "32",  trend: null,              trendUp: null,
    definition: "Conversation threads with at least one message in the last 7 days.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Alerts Pending",     value: "2",   trend: null,              trendUp: null,
    definition: "Scheduled announcements or emergency alerts waiting to be reviewed and sent.",
    dataSource: "Communications Module", dataHref: "/communications" },
];
export default function CommunicationsDirectorDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchCommunicationsMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  return (
    <CrownLayout title="Communications Director" subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Messages Sent (Week)"      value={data.messages_sent_week}        /></Col>
          <Col span={3}><CrownMetricCard label="Open Rate"                 value={`${data.open_rate_pct}%`}       /></Col>
          <Col span={3}><CrownMetricCard label="Announcements Scheduled"   value={data.announcements_scheduled}   /></Col>
          <Col span={3}><CrownMetricCard label="Unsubscribes (Week)"       value={data.unsubscribes_week}         /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Campaigns &amp; Channels">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Recent Campaigns">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Campaign', 'Sent', 'Open Rate', 'Status'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(data.campaigns || []).map((c, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{c.name}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{c.sent.toLocaleString()}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{c.open_rate}</td>
                      <td style={{ padding: '6px 8px' }}><Pill color={STATUS_PILL[c.status] || 'gray'}>{c.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Channel Engagement (MTD)">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(data.channel_engagement || []).map((ch, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4, color: 'var(--crown-ink)' }}>
                      <span>{ch.channel}</span><span style={{ fontWeight: 700 }}>{ch.open_rate}</span>
                    </div>
                    <div style={{ background: 'var(--crown-border)', borderRadius: 4, height: 8 }}>
                      <div style={{ background: 'var(--crown-brand)', borderRadius: 4, height: 8, width: `${Math.min(ch.pct, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Upcoming &amp; Alerts">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Upcoming Announcements">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Subject', 'Audience', 'Scheduled', 'Status'].map(h => (
                      <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(data.upcoming_announcements || []).map((a, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{a.subject}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)' }}>{a.audience}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)' }}>{a.scheduled}</td>
                      <td style={{ padding: '6px 8px' }}><Pill color={STATUS_PILL[a.status] || 'gray'}>{a.status}</Pill></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Alerts">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(data.alerts || []).map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
