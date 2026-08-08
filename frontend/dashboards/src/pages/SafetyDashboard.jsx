import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
import { authenticatedJson } from '../utils/authClient.js';

const DEMO = {
  total_incidents: 14, open_incidents: 5, resolved_incidents: 9, critical_open: 1,
  by_severity: [{ severity: 'low', count: 2 }, { severity: 'medium', count: 2 }, { severity: 'high', count: 0 }, { severity: 'critical', count: 1 }],
  by_category: [{ category: 'Slip/Fall', count: 4 }, { category: 'Medical', count: 3 }, { category: 'Behavioral', count: 3 }, { category: 'Property Damage', count: 2 }, { category: 'Security', count: 2 }],
  recent: [
    { id: '1', category: 'Behavioral', severity: 'critical', description: 'Physical altercation  hallway B2', resolved: false, created_at: '2026-02-22' },
    { id: '2', category: 'Medical', severity: 'medium', description: 'Allergic reaction at lunch', resolved: false, created_at: '2026-02-21' },
    { id: '3', category: 'Slip/Fall', severity: 'low', description: 'Student fell on wet stairs', resolved: true, created_at: '2026-02-20' },
    { id: '4', category: 'Security', severity: 'medium', description: 'Tailgate entry  side door', resolved: false, created_at: '2026-02-19' },
    { id: '5', category: 'Property Damage', severity: 'low', description: 'Broken window  classroom 14', resolved: true, created_at: '2026-02-18' },
  ],
};
const SEV_PILL = { low: 'green', medium: 'yellow', high: 'red', critical: 'red' };

async function fetchSafetyData() {
  try {
    const [metrics, listPayload] = await Promise.all([
      authenticatedJson('/api/v1/safety/metrics/'),
      authenticatedJson('/api/v1/safety/incidents/'),
    ]);
    const list = Array.isArray(listPayload) ? listPayload : (listPayload?.results || []);
    return { ok: true, data: { ...metrics, recent: list.slice(0, 10) } };
  } catch {
    return { ok: false, data: DEMO };
  }
}

function Pill({ color = 'gray', children }) {
  const map = {
    red: { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)' },
    yellow: { bg: 'var(--crown-warn-bg)', fg: 'var(--crown-warn)' },
    green: { bg: 'var(--crown-ok-bg)', fg: 'var(--crown-ok)' },
    gray: { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)' },
  };
  const v = map[color] || map.gray;
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 9px',
        fontSize: 11,
        fontWeight: 700,
        borderRadius: 999,
        background: v.bg,
        color: v.fg,
      }}
    >
      {children}
    </span>
  );
}

const ADMIN_KPI = [
  { label: "Incidents MTD", value: "2", trend: "-1 vs last mo", trendUp: true, definition: "Safety incidents (injury, near-miss, property damage) logged this month.", dataSource: "Safety Module", dataHref: "/safety" },
  { label: "Drills Completed", value: "3/5", trend: null, trendUp: null, definition: "Emergency drills (fire, lockdown, shelter-in-place) completed vs. scheduled this year.", dataSource: "Safety Module", dataHref: "/safety" },
  { label: "Visitors Today", value: "14", trend: null, trendUp: null, definition: "Visitors checked in through the front office visitor management system today.", dataSource: "Security Module", dataHref: "/security" },
  { label: "Open Hazards", value: "0", trend: null, trendUp: null, definition: "Reported safety hazards not yet resolved by facilities or administration.", dataSource: "Safety Module", dataHref: "/safety" },
];

export default function SafetyDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });
  useEffect(() => {
    fetchSafetyData().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);
  const { loading, live, data } = state;

  return (
    <CrownLayout
      title="Safety"
      subtitle="Campus incident tracking &amp; resolution"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}>
            <CrownMetricCard label="Total Incidents" value={data.total_incidents} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Open" value={data.open_incidents} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Resolved" value={data.resolved_incidents} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Critical Open" value={data.critical_open} />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Incidents">
        <CrownGrid>
          <Col span={4}>
            <CrownCard title="Open by Severity">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(data.by_severity || []).map((row, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '6px 0',
                      borderBottom: '1px solid var(--crown-border)',
                    }}
                  >
                    <Pill color={SEV_PILL[row.severity] || 'gray'}>{row.severity}</Pill>
                    <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--crown-ink)' }}>
                      {row.count}
                    </span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>

          <Col span={4}>
            <CrownCard title="Top Categories">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <tbody>
                  {(data.by_category || []).map((row, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>
                        {row.category}
                      </td>
                      <td
                        style={{
                          padding: '6px 8px',
                          textAlign: 'right',
                          fontWeight: 600,
                          color: 'var(--crown-ink)',
                        }}
                      >
                        {row.count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>

          <Col span={4}>
            <CrownCard title="Recent Incidents">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {(data.recent || []).slice(0, 5).map((inc, i) => (
                  <div
                    key={inc.id || i}
                    style={{ padding: '7px 0', borderBottom: '1px solid var(--crown-border)' }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: 3,
                      }}
                    >
                      <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--crown-ink)' }}>
                        {inc.category}
                      </span>
                      <Pill color={SEV_PILL[inc.severity] || 'gray'}>{inc.severity}</Pill>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--crown-muted)', marginBottom: 3 }}>
                      {inc.description}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: 11,
                        color: 'var(--crown-muted)',
                      }}
                    >
                      <span>{inc.created_at ? String(inc.created_at).slice(0, 10) : ''}</span>
                      <span
                        style={{
                          color: inc.resolved ? 'var(--crown-ok)' : 'var(--crown-danger)',
                          fontWeight: 600,
                        }}
                      >
                        {inc.resolved ? ' Resolved' : ' Open'}
                      </span>
                    </div>
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
