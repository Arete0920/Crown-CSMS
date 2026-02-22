import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

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
const PILL_COLORS = {
  red:    { background: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
  yellow: { background: '#fef9c3', color: '#854d0e', border: '#fde047' },
  green:  { background: '#dcfce7', color: '#166534', border: '#86efac' },
  gray:   { background: '#f3f4f6', color: '#374151', border: '#d1d5db' },
};
function Pill({ color = 'gray', children }) {
  const s = PILL_COLORS[color] || PILL_COLORS.gray;
  return (
    <span style={{
      display: 'inline-block', padding: '1px 8px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, border: `1px solid ${s.border}`,
      background: s.background, color: s.color, letterSpacing: 0.2,
    }}>{children}</span>
  );
}

function FunnelStep({ label, value, isLast }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        flex: 1, background: '#f8fafc', border: '1px solid #e5e7eb',
        borderRadius: 6, padding: '8px 12px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: 12, color: '#6b7280' }}>{label}</span>
        <span style={{ fontSize: 18, fontWeight: 800, color: '#111827' }}>{value}</span>
      </div>
      {!isLast && <span style={{ fontSize: 16, color: '#9ca3af', flexShrink: 0 }}>→</span>}
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────────── */
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
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      {/* ── KPI row ── */}
      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Inquiries YTD" value={data.inquiries_ytd ?? DEMO.inquiries_ytd} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Tours Scheduled" value={data.tours_scheduled ?? DEMO.tours_scheduled} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Applications" value={data.applications ?? DEMO.applications} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Enrolled" value={data.enrolled ?? DEMO.enrolled} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Inquiry Funnel ── */}
        <Col span={6}>
          <CrownCard title="Enrollment Funnel">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <FunnelStep label="Inquiries"  value={data.inquiries_ytd  ?? DEMO.inquiries_ytd}  isLast={false} />
              <FunnelStep label="Tours"      value={data.tours_scheduled ?? DEMO.tours_scheduled} isLast={false} />
              <FunnelStep label="Applied"    value={data.applications   ?? DEMO.applications}   isLast={false} />
              <FunnelStep label="Enrolled"   value={data.enrolled       ?? DEMO.enrolled}       isLast />
            </div>
          </CrownCard>
        </Col>

        {/* ── Source Mix ── */}
        <Col span={6}>
          <CrownCard title="Inquiry Source Mix">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {sources.map((s) => (
                <div key={s.source}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                    <span style={{ color: '#6b7280' }}>{s.source}</span>
                    <span><strong>{s.count}</strong> <span style={{ color: '#9ca3af' }}>({s.pct}%)</span></span>
                  </div>
                  <div style={{ height: 6, borderRadius: 4, background: '#f3f4f6', overflow: 'hidden' }}>
                    <div style={{ width: `${s.pct}%`, height: '100%', background: '#6366f1', borderRadius: 4 }} />
                  </div>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

        {/* ── Campaigns ── */}
        <Col span={6}>
          <CrownCard title="Campaign Performance">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #f3f4f6' }}>
                  <th style={{ padding: '4px 0' }}>Campaign</th>
                  <th style={{ padding: '4px 8px', textAlign: 'center' }}>Leads</th>
                  <th style={{ padding: '4px 0', textAlign: 'center' }}>Conv.</th>
                  <th style={{ padding: '4px 0', textAlign: 'right' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.name} style={{ borderBottom: '1px solid #f9fafb' }}>
                    <td style={{ padding: '6px 0', color: '#111827' }}>{c.name}</td>
                    <td style={{ padding: '6px 8px', textAlign: 'center', fontWeight: 700 }}>{c.leads}</td>
                    <td style={{ padding: '6px 0', textAlign: 'center', fontWeight: 700, color: '#22c55e' }}>{c.conversions}</td>
                    <td style={{ padding: '6px 0', textAlign: 'right' }}>
                      <Pill color={c.status === 'active' ? 'green' : 'gray'}>{c.status}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={6}>
          <CrownCard title="Alerts &amp; Stalled Leads">
            {alerts.length === 0
              ? <p style={{ fontSize: 13, color: '#22c55e' }}>No stalled leads — pipeline healthy.</p>
              : alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Pill color={a.severity}>{a.severity.toUpperCase()}</Pill>
                    <span style={{ fontSize: 13, color: '#374151' }}>{a.label}</span>
                  </div>
                ))
            }
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
