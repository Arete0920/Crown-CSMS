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
/* â”€â”€ Health / Nurse KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Students Seen Today", value: "4",  trend: null,              trendUp: null,
    definition: "Students who visited the health office today for any reason.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Medication Pending",  value: "2",  trend: null,              trendUp: null,
    definition: "Scheduled medication administrations not yet marked complete today.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Immunization Gaps",   value: "3",  trend: "-1 vs last wk",  trendUp: true,
    definition: "Students whose immunization records have outstanding or expiring requirements.",
    dataSource: "Health Module", dataHref: "/health" },
  { label: "Incidents MTD",       value: "8",  trend: null,              trendUp: null,
    definition: "Total health-related incidents logged this month (injury, illness, referral).",
    dataSource: "Health Module", dataHref: "/health" },
];
export default function HealthDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchHealthMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts       = data.alerts                   || DEMO.alerts;
  const todaysVisits = data.todays_visits            || DEMO.todays_visits;
  const medLog       = data.medication_log           || DEMO.medication_log;
  const immunComp    = data.immunization_compliance  || DEMO.immunization_compliance;

  const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
  const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

  return (
    <CrownLayout
      title="Health / Nurse"
      subtitle="Daily visits, medications, immunization compliance, and incident tracking"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading…</p>}

      {/* ── Section 1: Overview KPIs ── */}
      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}>
            <CrownMetricCard label="Visits Today"          value={data.visits_today          ?? DEMO.visits_today} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Meds Administered"     value={data.meds_administered     ?? DEMO.meds_administered} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Immunizations Missing" value={data.immunizations_missing  ?? DEMO.immunizations_missing} />
          </Col>
          <Col span={3}>
            <CrownMetricCard label="Incidents (This Week)" value={data.incident_reports_week  ?? DEMO.incident_reports_week} />
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Section 2: Daily Activity ── */}
      <DashboardSection title="Daily Activity">
        <CrownGrid>
          {/* Today's Visits */}
          <Col span={6}>
            <CrownCard title="Today's Visits">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Student', 'Gr', 'Reason', 'Time', 'Disposition'].map(h => (
                      <th key={h} style={TH}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {todaysVisits.map((v, i) => (
                    <tr key={i}>
                      <td style={{ ...TD, fontWeight: 500 }}>{v.name}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{v.grade}</td>
                      <td style={TD}>{v.reason}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)', whiteSpace: 'nowrap' }}>{v.time}</td>
                      <td style={TD}>{v.disposition}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>

          {/* Medication Log Summary */}
          <Col span={6}>
            <CrownCard title="Medication Log Summary">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    {['Medication', 'Students', 'Doses Given'].map(h => (
                      <th key={h} style={TH}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {medLog.map((m, i) => (
                    <tr key={i}>
                      <td style={{ ...TD, fontWeight: 500 }}>{m.medication}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{m.students}</td>
                      <td style={{ ...TD, color: m.doses_given > 0 ? 'var(--crown-ok)' : 'var(--crown-muted)' }}>{m.doses_given}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      {/* ── Section 3: Compliance & Alerts ── */}
      <DashboardSection title="Compliance & Alerts">
        <CrownGrid>
          {/* Immunization Compliance by Grade */}
          <Col span={6}>
            <CrownCard title="Immunization Compliance by Grade">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {immunComp.map((g, i) => {
                  const total = g.compliant + g.missing;
                  const pct   = total ? Math.round((g.compliant / total) * 100) : 100;
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                        <span style={{ fontWeight: 500, color: 'var(--crown-ink)' }}>{g.grade}</span>
                        <span style={{ color: g.missing > 0 ? 'var(--crown-danger)' : 'var(--crown-ok)' }}>
                          {pct}% — {g.missing > 0 ? `${g.missing} missing` : 'complete'}
                        </span>
                      </div>
                      <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                        <div style={{ height: '100%', borderRadius: 4, width: `${pct}%`,
                          background: g.missing > 0 ? 'var(--crown-warn)' : 'var(--crown-ok)' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CrownCard>
          </Col>

          {/* Alerts */}
          <Col span={6}>
            <CrownCard title="Alerts &amp; Action Items">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
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
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
