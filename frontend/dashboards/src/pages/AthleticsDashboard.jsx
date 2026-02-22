import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

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
  upcoming_events:      6,
  eligibility_issues:   3,
  injuries_count:       2,
  transportation_needs: 4,
  week_schedule: [
    { sport: "Boys Basketball",  opponent: "Westside Prep",    date: "Feb 22", time: "4:00 PM", home: true },
    { sport: "Girls Soccer",     opponent: "Eastview Academy", date: "Feb 23", time: "10:00 AM", home: false },
    { sport: "Track & Field",    opponent: "Invitational",     date: "Feb 24", time: "8:00 AM",  home: false },
    { sport: "Boys Soccer",      opponent: "Hillside School",  date: "Feb 25", time: "4:30 PM", home: true },
    { sport: "Swimming",         opponent: "State Qualifier",  date: "Feb 26", time: "9:00 AM",  home: false },
  ],
  eligibility_watch: [
    { sport: "Boys Basketball", count: 1, issue: "GPA below 2.0" },
    { sport: "Football",        count: 1, issue: "Missing physical" },
    { sport: "Track & Field",   count: 1, issue: "Missing consent form" },
  ],
  roster_compliance: [
    { sport: "Boys Basketball", roster: 12, forms_complete: 11, physicals_ok: 12 },
    { sport: "Girls Soccer",    roster: 16, forms_complete: 16, physicals_ok: 15 },
    { sport: "Track & Field",   roster: 22, forms_complete: 21, physicals_ok: 22 },
    { sport: "Swimming",        roster: 14, forms_complete: 14, physicals_ok: 14 },
  ],
  alerts: [
    { label: "1 eligibility hold — Boys Basketball roster may be short Saturday",  severity: "red"    },
    { label: "Missing physical: Girls Soccer — Mia Torres (parent notified)",      severity: "yellow" },
    { label: "Track consent form missing — deadline Feb 23",                       severity: "yellow" },
    { label: "4 away game transport requests need driver confirmation",             severity: "yellow" },
  ],
};

async function fetchAthleticsMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/athletics/metrics/`;
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

export default function AthleticsDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchAthleticsMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts      = data.alerts              || DEMO.alerts;
  const schedule    = data.week_schedule       || DEMO.week_schedule;
  const eligWatch   = data.eligibility_watch   || DEMO.eligibility_watch;
  const compliance  = data.roster_compliance   || DEMO.roster_compliance;

  return (
    <CrownLayout
      title="Athletic Director"
      subtitle="Events, eligibility, roster compliance, and transportation"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Upcoming Events"       value={data.upcoming_events      ?? DEMO.upcoming_events} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Eligibility Issues"    value={data.eligibility_issues   ?? DEMO.eligibility_issues} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Injuries (Active)"     value={data.injuries_count       ?? DEMO.injuries_count} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Transport Needs"       value={data.transportation_needs ?? DEMO.transportation_needs} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── This Week Schedule ── */}
        <Col span={8}>
          <CrownCard title="This Week's Schedule">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Sport', 'Opponent', 'Date', 'Time', 'Location'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {schedule.map((e, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{e.sport}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{e.opponent}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280', whiteSpace: 'nowrap' }}>{e.date}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{e.time}</td>
                    <td style={{ padding: '6px 8px' }}><Pill color={e.home ? 'green' : 'gray'}>{e.home ? 'Home' : 'Away'}</Pill></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Eligibility Watch ── */}
        <Col span={4}>
          <CrownCard title="Eligibility Watch List">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {eligWatch.map((e, i) => (
                <div key={i} style={{
                  padding: '8px 12px', borderRadius: 6, background: '#fee2e2',
                  border: '1px solid #fca5a5',
                }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{e.sport}</div>
                  <div style={{ fontSize: 12, color: '#991b1b' }}>{e.count} student — {e.issue}</div>
                </div>
              ))}
              {eligWatch.length === 0 && (
                <p style={{ fontSize: 13, color: '#16a34a' }}>All athletes eligible ✓</p>
              )}
            </div>
          </CrownCard>
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Roster Compliance ── */}
        <Col span={6}>
          <CrownCard title="Roster Compliance">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Sport', 'Roster', 'Forms', 'Physicals'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {compliance.map((c, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{c.sport}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{c.roster}</td>
                    <td style={{ padding: '6px 8px' }}>
                      <span style={{ color: c.forms_complete < c.roster ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                        {c.forms_complete}/{c.roster}
                      </span>
                    </td>
                    <td style={{ padding: '6px 8px' }}>
                      <span style={{ color: c.physicals_ok < c.roster ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                        {c.physicals_ok}/{c.roster}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={6}>
          <CrownCard title="Alerts &amp; Action Items">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {alerts.map((a, i) => (
                <div key={i} style={{
                  padding: '8px 12px', borderRadius: 6,
                  background: a.severity === 'red' ? '#fee2e2' : a.severity === 'yellow' ? '#fef9c3' : '#f3f4f6',
                  border: `1px solid ${a.severity === 'red' ? '#fca5a5' : a.severity === 'yellow' ? '#fde047' : '#e5e7eb'}`,
                }}>
                  <span style={{ fontSize: 13, color: a.severity === 'red' ? '#991b1b' : a.severity === 'yellow' ? '#854d0e' : '#374151' }}>
                    {a.label}
                  </span>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
