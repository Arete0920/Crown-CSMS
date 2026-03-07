import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection   from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

/* ── Auth helpers ─────────────────────────────────────────────────────── */
function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token:    sessionStorage.getItem('crown.jwt.access') || '',
      schoolId: sessionStorage.getItem('crown.school.id')  || '',
    };
  } catch { return { token: '', schoolId: '' }; }
}

/* ── Static demo fallback ─────────────────────────────────────────────── */
const DEMO = {
  inquiries_ytd:  187,
  tours_scheduled: 62,
  applications:    54,
  enrolled:        38,
  inquiry_sources: [
    { source: 'Website',     count: 74, pct: 40 },
    { source: 'Referral',    count: 56, pct: 30 },
    { source: 'Social',      count: 37, pct: 20 },
    { source: 'Event',       count: 20, pct: 10 },
  ],
  campaigns: [
    { name: 'Spring Open House', status: 'active',   leads: 28, conversions: 9  },
    { name: 'Digital Ads Q1',    status: 'active',   leads: 41, conversions: 12 },
    { name: 'Referral Drive',    status: 'complete', leads: 18, conversions: 7  },
  ],
  stalled_leads: 11,
  alerts: [
    { label: '11 leads with no follow-up >7 days', severity: 'red'    },
    { label: 'Open House RSVPs below target (28/50)', severity: 'yellow' },
  ],
};

async function fetchMarketingMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/marketing/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: DEMO };
  }
}

/* ── Helpers ──────────────────────────────────────────────────────────── */
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

function FunnelStep({ label, value, isLast }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        flex: 1, background: 'var(--crown-surface-2)', border: '1px solid var(--crown-border)',
        borderRadius: 6, padding: '8px 12px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: 12, color: 'var(--crown-muted)' }}>{label}</span>
        <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--crown-ink)' }}>{value}</span>
      </div>
      {!isLast && <span style={{ fontSize: 16, color: 'var(--crown-muted)', flexShrink: 0 }}>→</span>}
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────────── */
/* â”€â”€ Marketing KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Inquiries MTD",     value: "28",    trend: "+6 vs last mo",  trendUp: true,
    definition: "Prospective families who submitted an inquiry form this month.",
    dataSource: "Admissions / CRM", dataHref: "/admissions" },
  { label: "Website Visits",    value: "1,842", trend: "+14% vs last mo",trendUp: true,
    definition: "Total unique visitors to the school website this calendar month.",
    dataSource: "Analytics", dataHref: "/marketing" },
  { label: "Email Open Rate",   value: "42%",   trend: "+3% vs last mo", trendUp: true,
    definition: "Average open rate across all marketing emails sent this month.",
    dataSource: "Communications Module", dataHref: "/communications" },
  { label: "Social Followers",  value: "2,140", trend: "+32 this mo",    trendUp: true,
    definition: "Total combined followers across all official school social media accounts.",
    dataSource: "Marketing Module", dataHref: "/marketing" },
];
export default function MarketingDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchMarketingMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const sources = data.inquiry_sources || DEMO.inquiry_sources;
  const campaigns = data.campaigns || DEMO.campaigns;
  const alerts = data.alerts || DEMO.alerts;

  return (
    <CrownLayout
      title="Marketing &amp; Advancement"
      subtitle="Enrollment funnel, campaign performance, and lead pipeline"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Inquiries YTD" value={data.inquiries_ytd ?? DEMO.inquiries_ytd} /></Col>
          <Col span={3}><CrownMetricCard label="Tours Scheduled" value={data.tours_scheduled ?? DEMO.tours_scheduled} /></Col>
          <Col span={3}><CrownMetricCard label="Applications" value={data.applications ?? DEMO.applications} /></Col>
          <Col span={3}><CrownMetricCard label="Enrolled" value={data.enrolled ?? DEMO.enrolled} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Enrollment Funnel">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Enrollment Funnel">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <FunnelStep label="Inquiries" value={data.inquiries_ytd ?? DEMO.inquiries_ytd} isLast={false} />
                <FunnelStep label="Tours" value={data.tours_scheduled ?? DEMO.tours_scheduled} isLast={false} />
                <FunnelStep label="Applied" value={data.applications ?? DEMO.applications} isLast={false} />
                <FunnelStep label="Enrolled" value={data.enrolled ?? DEMO.enrolled} isLast />
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Inquiry Source Mix">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sources.map((s) => (
                  <div key={s.source}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                      <span style={{ color: 'var(--crown-muted)' }}>{s.source}</span>
                      <span><strong>{s.count}</strong> <span style={{ color: 'var(--crown-muted)' }}>({s.pct}%)</span></span>
                    </div>
                    <div style={{ height: 6, borderRadius: 4, background: 'var(--crown-surface-2)', overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${s.pct}%`, height: '100%', background: 'var(--crown-brand)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Campaigns &amp; Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Campaign Performance">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    <th style={{ padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>Campaign</th>
                    <th style={{ padding: '7px 10px', textAlign: 'center', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>Leads</th>
                    <th style={{ padding: '7px 10px', textAlign: 'center', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>Conv.</th>
                    <th style={{ padding: '7px 10px', textAlign: 'right', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c) => (
                    <tr key={c.name}>
                      <td style={{ padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' }}>{c.name}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 700, color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' }}>{c.leads}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 700, color: 'var(--crown-ok)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' }}>{c.conversions}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontSize: 13, borderBottom: '1px solid var(--crown-border)' }}>
                        <Pill color={c.status === 'active' ? 'green' : 'gray'}>{c.status}</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts &amp; Stalled Leads">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.length === 0
                  ? <p style={{ fontSize: 13, color: 'var(--crown-ok)' }}>No stalled leads — pipeline healthy.</p>
                  : alerts.map((a, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                        background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                        border: '1px solid var(--crown-border)' }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                          background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                        <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                      </div>
                    ))
                }
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
