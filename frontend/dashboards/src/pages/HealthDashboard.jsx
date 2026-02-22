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
  visits_today:            14,
  meds_administered:        9,
  immunizations_missing:    6,
  incident_reports_week:    2,
  todays_visits: [
    { name: 'Elijah Turner',   grade: '9',  reason: 'Headache',     time: '8:12 AM',  disposition: 'Sent home' },
    { name: 'Sofia Medina',    grade: '11', reason: 'Stomach ache',  time: '9:45 AM',  disposition: 'Returned to class' },
    { name: 'Marcus Brown',    grade: '7',  reason: 'Inhaler (asthma)', time: '10:30 AM', disposition: 'Returned to class' },
    { name: 'Ava Chen',        grade: '10', reason: 'Ankle twist – PE', time: '11:05 AM', disposition: 'Ice + rest period' },
    { name: 'Noah Williams',   grade: '8',  reason: 'Medication pickup', time: '12:00 PM', disposition: 'Completed' },
  ],
  medication_log: [
    { medication: 'Albuterol inhaler', students: 3, doses_given: 3 },
    { medication: 'EpiPen (on file)',  students: 1, doses_given: 0 },
    { medication: 'ADHD daily med',    students: 4, doses_given: 4 },
    { medication: 'Insulin injection', students: 1, doses_given: 1 },
  ],
  immunization_compliance: [
    { grade: 'Grade 7',  compliant: 24, missing: 2 },
    { grade: 'Grade 8',  compliant: 26, missing: 1 },
    { grade: 'Grade 9',  compliant: 28, missing: 1 },
    { grade: 'Grade 10', compliant: 25, missing: 2 },
    { grade: 'Grade 11', compliant: 27, missing: 0 },
    { grade: 'Grade 12', compliant: 23, missing: 0 },
  ],
  alerts: [
    { label: '2 student physicals expire this month',              severity: 'yellow' },
    { label: '6 immunization records incomplete — parent follow-up needed', severity: 'red' },
    { label: '1 pending parent callback — Sofia Medina (sent home)', severity: 'yellow' },
    { label: 'Inhaler stock — refill needed this week',            severity: 'gray'   },
  ],
};

async function fetchHealthMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/health/metrics/`;
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
export default function HealthDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchHealthMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts         = data.alerts         || DEMO.alerts;
  const todaysVisits   = data.todays_visits  || DEMO.todays_visits;
  const medLog         = data.medication_log || DEMO.medication_log;
  const immunComp      = data.immunization_compliance || DEMO.immunization_compliance;

  return (
    <CrownLayout
      title="Health / Nurse"
      subtitle="Daily visits, medications, immunization compliance, and incident tracking"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      {loading && <p style={{ color: '#6b7280', padding: 16 }}>Loading…</p>}

      {/* ── KPI row ── */}
      <CrownGrid>
        <Col span={3}>
          <CrownMetricCard label="Visits Today"             value={data.visits_today             ?? DEMO.visits_today} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Meds Administered"        value={data.meds_administered        ?? DEMO.meds_administered} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Immunizations Missing"    value={data.immunizations_missing    ?? DEMO.immunizations_missing} />
        </Col>
        <Col span={3}>
          <CrownMetricCard label="Incidents (This Week)"    value={data.incident_reports_week    ?? DEMO.incident_reports_week} />
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Today's Visits ── */}
        <Col span={6}>
          <CrownCard title="Today's Visits">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Student', 'Gr', 'Reason', 'Time', 'Disposition'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {todaysVisits.map((v, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{v.name}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{v.grade}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{v.reason}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280', whiteSpace: 'nowrap' }}>{v.time}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{v.disposition}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Medication Log Summary ── */}
        <Col span={6}>
          <CrownCard title="Medication Log Summary">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Medication', 'Students', 'Doses Given'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: 12 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {medLog.map((m, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{m.medication}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{m.students}</td>
                    <td style={{ padding: '6px 8px', color: m.doses_given > 0 ? '#166534' : '#9ca3af' }}>{m.doses_given}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>
      </CrownGrid>

      <CrownGrid style={{ marginTop: 16 }}>
        {/* ── Immunization Compliance ── */}
        <Col span={6}>
          <CrownCard title="Immunization Compliance by Grade">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {immunComp.map((g, i) => {
                const total = g.compliant + g.missing;
                const pct   = total ? Math.round((g.compliant / total) * 100) : 100;
                return (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                      <span style={{ fontWeight: 500 }}>{g.grade}</span>
                      <span style={{ color: g.missing > 0 ? '#dc2626' : '#16a34a' }}>
                        {pct}% — {g.missing > 0 ? `${g.missing} missing` : 'complete'}
                      </span>
                    </div>
                    <div style={{ height: 6, background: '#e5e7eb', borderRadius: 4 }}>
                      <div style={{ height: 6, borderRadius: 4, width: `${pct}%`, background: g.missing > 0 ? '#f59e0b' : '#22c55e' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </CrownCard>
        </Col>

        {/* ── Alerts ── */}
        <Col span={6}>
          <CrownCard title="Alerts &amp; Action Items">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {alerts.map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
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
