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

/* ── Main component ───────────────────────────────────────────────────── */
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

  return (
    <CrownLayout
      title="Spiritual Life"
      subtitle="Chapel program, service hours, and pastoral care"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      {/* ── KPI row ── */}
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

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Upcoming Chapel ── */}
        <Col span={6}>
          <CrownCard title="Upcoming Chapel Schedule">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #f3f4f6' }}>
                  <th style={{ padding: '4px 0' }}>Date</th>
                  <th style={{ padding: '4px 8px' }}>Topic</th>
                  <th style={{ padding: '4px 0' }}>Speaker</th>
                </tr>
              </thead>
              <tbody>
                {upcoming.map((u) => (
                  <tr key={u.date} style={{ borderBottom: '1px solid #f9fafb' }}>
                    <td style={{ padding: '6px 0', fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>{u.date}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{u.topic}</td>
                    <td style={{ padding: '6px 0', color: '#6b7280', fontSize: 11 }}>{u.speaker}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Service Hours ── */}
        <Col span={6}>
          <CrownCard title="Service Hours YTD">
            <div style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: '#6b7280' }}>Progress toward annual goal</span>
                <strong>{serviceGoalPct}%</strong>
              </div>
              <div style={{ height: 10, borderRadius: 5, background: '#f3f4f6', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(serviceGoalPct, 100)}%`, height: '100%', background: '#6366f1', borderRadius: 5 }} />
              </div>
              <p style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>
                {data.service_hours_ytd ?? DEMO.service_hours_ytd} of {data.service_hours_goal ?? DEMO.service_hours_goal} hours
              </p>
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: 13 }}>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Referrals resolved (month)</div>
                <strong style={{ fontSize: 20 }}>{data.care_referrals_resolved_mtd ?? DEMO.care_referrals_resolved_mtd}</strong>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Students flagged for support</div>
                <strong style={{ fontSize: 20, color: (data.support_flagged_students ?? DEMO.support_flagged_students) > 0 ? '#f59e0b' : '#22c55e' }}>
                  {data.support_flagged_students ?? DEMO.support_flagged_students}
                </strong>
              </div>
            </div>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={12}>
          <CrownCard title="Pastoral Alerts">
            {alerts.length === 0
              ? <p style={{ fontSize: 13, color: '#22c55e' }}>No active pastoral alerts.</p>
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
