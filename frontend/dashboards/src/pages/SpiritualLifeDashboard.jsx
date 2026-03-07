import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
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
  chapel_sessions_this_month: 8,
  avg_chapel_attendance_pct:  91,
  service_hours_ytd:          1240,
  service_hours_goal:         2000,
  care_referrals_open:        4,
  care_referrals_resolved_mtd: 11,
  support_flagged_students:   3,
  upcoming_chapel: [
    { date: 'Feb 24', topic: 'Faith in Community',  speaker: 'Chaplain Davis' },
    { date: 'Feb 26', topic: 'Service & Calling',   speaker: 'Guest — Rev. Park' },
    { date: 'Mar 3',  topic: 'Chapel Worship Night', speaker: 'Student Led'    },
  ],
  alerts: [
    { label: '3 students flagged for pastoral follow-up', severity: 'yellow' },
    { label: '4 open care referrals pending assignment',  severity: 'yellow' },
  ],
};

async function fetchSpiritualLifeMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/spiritual-life/metrics/`;
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
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

/* ── Main component ───────────────────────────────────────────────────── */
/* â”€â”€ Spiritual Life KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Chapel Attendance",  value: "94%",  trend: "+2% vs last wk",  trendUp: true,
    definition: "Percentage of enrolled students present at the most recent chapel service.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Service Hours",      value: "847",  trend: "+112 MTD",         trendUp: true,
    definition: "Total community service hours logged by students this academic year.",
    dataSource: "Service Hours Module", dataHref: "/service-hours" },
  { label: "Events This Month",  value: "3",    trend: null,               trendUp: null,
    definition: "Spiritual life events (retreats, guest speakers, prayer events) scheduled this month.",
    dataSource: "Calendar Module", dataHref: "/calendar" },
  { label: "Devotions Sent",     value: "14",   trend: null,               trendUp: null,
    definition: "Daily devotions and reflections distributed to staff and families this term.",
    dataSource: "Communications Module", dataHref: "/communications" },
];
export default function SpiritualLifeDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchSpiritualLifeMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const upcoming = data.upcoming_chapel || DEMO.upcoming_chapel;
  const alerts   = data.alerts          || DEMO.alerts;
  const serviceGoalPct = data.service_hours_goal
    ? Math.round((data.service_hours_ytd / data.service_hours_goal) * 100)
    : 0;

  const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
  const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

  return (
    <CrownLayout
      title="Spiritual Life"
      subtitle="Chapel program, service hours, and pastoral care"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      {/* ── Section 1: Overview KPIs ── */}
      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}>
            <CrownMetricCard label="Chapel Sessions (month)" value={data.chapel_sessions_this_month ?? DEMO.chapel_sessions_this_month} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Avg Attendance" value={`${data.avg_chapel_attendance_pct ?? DEMO.avg_chapel_attendance_pct}%`} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Service Hours YTD" value={data.service_hours_ytd ?? DEMO.service_hours_ytd} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Open Care Referrals" value={data.care_referrals_open ?? DEMO.care_referrals_open} />
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Section 2: Chapel & Service ── */}
      <DashboardSection title="Chapel & Service">
        <CrownGrid>
          {/* Upcoming Chapel Schedule */}
          <Col span={6}>
            <CrownCard title="Upcoming Chapel Schedule">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    <th style={TH}>Date</th>
                    <th style={TH}>Topic</th>
                    <th style={TH}>Speaker</th>
                  </tr>
                </thead>
                <tbody>
                  {upcoming.map((u) => (
                    <tr key={u.date}>
                      <td style={{ ...TD, fontWeight: 700, whiteSpace: 'nowrap' }}>{u.date}</td>
                      <td style={TD}>{u.topic}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)', fontSize: 11 }}>{u.speaker}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>

          {/* Service Hours */}
          <Col span={6}>
            <CrownCard title="Service Hours YTD">
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: 'var(--crown-muted)' }}>Progress toward annual goal</span>
                  <strong>{serviceGoalPct}%</strong>
                </div>
                <div style={{ height: 10, borderRadius: 5, background: 'var(--crown-surface-2)', overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                  <div style={{ width: `${Math.min(serviceGoalPct, 100)}%`, height: '100%', background: 'var(--crown-brand)', borderRadius: 5 }} />
                </div>
                <p style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4 }}>
                  {data.service_hours_ytd ?? DEMO.service_hours_ytd} of {data.service_hours_goal ?? DEMO.service_hours_goal} hours
                </p>
              </div>
              <div style={{ display: 'flex', gap: 24, fontSize: 13 }}>
                <div>
                  <div style={{ color: 'var(--crown-muted)', fontSize: 11 }}>Referrals resolved (month)</div>
                  <strong style={{ fontSize: 20, color: 'var(--crown-ink)' }}>{data.care_referrals_resolved_mtd ?? DEMO.care_referrals_resolved_mtd}</strong>
                </div>
                <div>
                  <div style={{ color: 'var(--crown-muted)', fontSize: 11 }}>Students flagged for support</div>
                  <strong style={{ fontSize: 20, color: (data.support_flagged_students ?? DEMO.support_flagged_students) > 0 ? 'var(--crown-warn)' : 'var(--crown-ok)' }}>
                    {data.support_flagged_students ?? DEMO.support_flagged_students}
                  </strong>
                </div>
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Section 3: Pastoral Alerts ── */}
      <DashboardSection title="Pastoral Alerts">
        <CrownGrid>
          <Col span={12}>
            <CrownCard title="Pastoral Alerts">
              {alerts.length === 0
                ? <p style={{ fontSize: 13, color: 'var(--crown-ok)' }}>No active pastoral alerts.</p>
                : <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {alerts.map((a, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                        background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                        border: '1px solid var(--crown-border)',
                      }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                          background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                        <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                      </div>
                    ))}
                  </div>
              }
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
