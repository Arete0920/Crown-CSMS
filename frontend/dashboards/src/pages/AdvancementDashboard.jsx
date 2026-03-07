import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection   from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

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

const DEMO = {
  donors_active:          127,
  campaign_progress_pct:   64,
  pledges_outstanding:     23,
  thankyous_due:            9,
  campaigns: [
    { name: 'Annual Fund 2026',     goal: 150000, raised: 96000,  donors: 87, status: 'active'   },
    { name: 'Capital Campaign',     goal: 500000, raised: 212000, donors: 44, status: 'active'   },
    { name: 'Scholarship Endowment',goal: 75000,  raised: 74800,  donors: 38, status: 'closing'  },
    { name: 'Spring Gala 2026',     goal: 40000,  raised: 4800,   donors: 12, status: 'upcoming' },
  ],
  top_sources: [
    { source: 'Alumni',          amount: 48200 },
    { source: 'Current Families',amount: 62400 },
    { source: 'Foundations',     amount: 32000 },
    { source: 'Corporate',       amount: 19800 },
    { source: 'Board',           amount: 15000 },
  ],
  tasks: [
    { task: 'Thank-you notes — Annual Fund (Feb batch)', due: 'Feb 23', priority: 'high' },
    { task: 'Pledge follow-up call list — 5 lapsed donors', due: 'Feb 25', priority: 'high' },
    { task: 'Board solicitation packets prepared',        due: 'Feb 28', priority: 'normal' },
    { task: 'Matching-gift deadline — Johnson Foundation', due: 'Mar 1',  priority: 'high' },
    { task: 'Stewardship report — Capital Campaign Q1',   due: 'Mar 7',  priority: 'normal' },
  ],
  alerts: [
    { label: '9 thank-you notes overdue — 5+ days since gift received',      severity: 'red'    },
    { label: 'Johnson Foundation matching-gift deadline Mar 1 — 6 unclaimed', severity: 'yellow' },
    { label: '23 open pledges outstanding — follow-up queue ready',           severity: 'yellow' },
    { label: 'Scholarship Endowment nearly closed — final push opportunity',  severity: 'gray'   },
  ],
};

async function fetchAdvancementMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/advancement/metrics/`;
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

function Pill({ color = 'gray', children }) {
  const map = {
    red:    { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)'  },
    yellow: { bg: 'var(--crown-warn-bg)',   fg: 'var(--crown-warn)'    },
    green:  { bg: 'var(--crown-ok-bg)',     fg: 'var(--crown-ok)'      },
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

const STATUS_COLOR = { active: 'green', closing: 'yellow', upcoming: 'gray' };
const fmt = n => `$${n.toLocaleString()}`;

/* â”€â”€ Advancement KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Active Donors",       value: "127",     trend: "+14 vs last yr", trendUp: true,
    definition: "Unique donors who have given at least one gift in the current fiscal year.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Campaign Progress",   value: "64%",     trend: "+18% MTD",       trendUp: true,
    definition: "Weighted average of progress across all active campaigns (raised ÷ goal).",
    dataSource: "Campaign Scoreboard", dataHref: "/advancement" },
  { label: "YTD Raised",          value: "$177,400", trend: null,             trendUp: null,
    definition: "Total gifts and pledges received year-to-date across all campaigns.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Pledges Outstanding", value: "23",      trend: null,             trendUp: null,
    definition: "Number of pledge commitments not yet fulfilled — follow-up queue ready.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
  { label: "Thank-Yous Due",      value: "9",       trend: null,             trendUp: null,
    definition: "Acknowledgement letters or calls not yet completed within the 48-hr stewardship window.",
    dataSource: "Advancement Module", dataHref: "/advancement" },
];
export default function AdvancementDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchAdvancementMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts    = data.alerts      || DEMO.alerts;
  const campaigns = data.campaigns   || DEMO.campaigns;
  const sources   = data.top_sources || DEMO.top_sources;
  const tasks     = data.tasks       || DEMO.tasks;
  const maxSource = Math.max(...sources.map(s => s.amount), 1);

  return (
    <CrownLayout
      title="Advancement &amp; Fundraising"
      subtitle="Campaign progress, donor stewardship, pledges, and task queue"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Active Donors" value={data.donors_active ?? DEMO.donors_active} /></Col>
          <Col span={3}><CrownMetricCard label="Campaign Progress" value={`${data.campaign_progress_pct ?? DEMO.campaign_progress_pct}%`} /></Col>
          <Col span={3}><CrownMetricCard label="Pledges Outstanding" value={data.pledges_outstanding ?? DEMO.pledges_outstanding} /></Col>
          <Col span={3}><CrownMetricCard label="Thank-Yous Due" value={data.thankyous_due ?? DEMO.thankyous_due} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Campaign Scoreboard">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Campaign Scoreboard">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {campaigns.map((c, i) => {
                  const pct = Math.round((c.raised / c.goal) * 100);
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, fontSize: 13 }}>
                        <span style={{ fontWeight: 600, color: 'var(--crown-ink)' }}>{c.name}</span>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ color: 'var(--crown-muted)', fontSize: 12 }}>{fmt(c.raised)} / {fmt(c.goal)}</span>
                          <Pill color={STATUS_COLOR[c.status] || 'gray'}>{c.status}</Pill>
                        </div>
                      </div>
                      <div style={{ height: 8, background: 'var(--crown-border)', borderRadius: 4 }}>
                        <div style={{ height: 8, borderRadius: 4, width: `${Math.min(pct, 100)}%`,
                          background: pct >= 100 ? 'var(--crown-ok)' : pct >= 60 ? 'var(--crown-brand)' : 'var(--crown-warn)' }} />
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 2 }}>{pct}% — {c.donors} donors</div>
                    </div>
                  );
                })}
              </div>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Top Giving Sources (YTD)">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sources.map((s, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                      <span style={{ fontWeight: 500, color: 'var(--crown-ink)' }}>{s.source}</span>
                      <span style={{ color: 'var(--crown-ink)' }}>{fmt(s.amount)}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-border)', borderRadius: 4 }}>
                      <div style={{ height: 6, borderRadius: 4, width: `${Math.round((s.amount / maxSource) * 100)}%`, background: 'var(--crown-brand)' }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Tasks &amp; Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Tasks Queue">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {tasks.map((t, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '7px 10px', borderRadius: 5,
                    background: t.priority === 'high' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                    border: '1px solid var(--crown-border)',
                  }}>
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{t.task}</span>
                    <span style={{ fontSize: 11, color: 'var(--crown-muted)', whiteSpace: 'nowrap', marginLeft: 8 }}>Due {t.due}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts &amp; Stewardship">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.map((a, i) => (
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
