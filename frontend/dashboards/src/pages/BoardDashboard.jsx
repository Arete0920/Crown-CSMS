import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

/* ── Auth helpers ────────────────────────────────────────────────────── */
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

/* ── Static demo fallback ────────────────────────────────────────────── */
const DEMO = {
  enrollment: { current: 312, target: 340, waitlist: 23, retention_pct: 91.2 },
  finance_health: {
    tuition_billed:    2_180_000,
    tuition_collected: 1_943_000,
    collection_pct:    89.1,
    aid_awarded:       312_500,
    ar_90_plus:        48_200,
  },
  mission: {
    survey_pulse_avg:      4.3,
    service_hours_ytd:     1842,
    chapel_attendance_pct: 94,
  },
  compliance: {
    safety_incidents_ytd:    2,
    audit_log_entries_30d:   5841,
    required_checks_passing: 7,
  },
};

async function fetchBoardMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/board/metrics/`;
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

function fmt$(n) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0,
  }).format(n);
}

/* ── Pill ────────────────────────────────────────────────────────────── */
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

/* ── Progress bar ────────────────────────────────────────────────────── */
function ProgressBar({ pct, color = 'var(--crown-brand)' }) {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div style={{ height: 6, background: 'var(--crown-border)', borderRadius: 3, overflow: 'hidden', marginTop: 4 }}>
      <div style={{ height: '100%', width: `${clamped}%`, background: color, borderRadius: 3, transition: 'width 0.4s' }} />
    </div>
  );
}

/* ── StatRow ─────────────────────────────────────────────────────────── */
function StatRow({ label, value, sub }) {
  return (
    <tr style={{ borderBottom: '1px solid var(--crown-border)' }}>
      <td style={{ padding: '8px 0', color: 'var(--crown-muted)', fontSize: 13 }}>{label}</td>
      <td style={{ padding: '8px 0', textAlign: 'right' }}>
        <span style={{ fontWeight: 700, color: 'var(--crown-ink)', fontSize: 14 }}>{value}</span>
        {sub && <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--crown-muted)' }}>{sub}</span>}
      </td>
    </tr>
  );
}

/* ── Main component ─────────────────────────────────────────────────── */
/* â”€â”€ Board KPI flip cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Enrollment",         value: "742",    trend: "+4.1% vs goal",    trendUp: true,
    definition: "Total active student enrollment for the current academic year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Net Tuition Rev",    value: "$6.8M",  trend: "+10% vs last yr",  trendUp: true,
    definition: "Gross tuition collected minus total financial aid awarded — year-to-date.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Staff Retention",    value: "94%",    trend: "+2% vs last yr",   trendUp: true,
    definition: "Percentage of employees who remained from the start to current date this year.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Endowment Balance",  value: "$2.1M",  trend: "+$80K vs last yr", trendUp: true,
    definition: "Current endowment fund balance including investment returns and new gifts.",
    dataSource: "Finance Module", dataHref: "/finance" },
];
export default function BoardDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchBoardMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const enr  = data.enrollment    || DEMO.enrollment;
  const fin  = data.finance_health || DEMO.finance_health;
  const mis  = data.mission        || DEMO.mission;
  const comp = data.compliance     || DEMO.compliance;

  const enrollPct = enr.target ? Math.round((enr.current / enr.target) * 100) : 0;

  return (
    <CrownLayout title="School Board" subtitle="Governance · mission · finance oversight"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      <DashboardSection title="Key Indicators">
        <CrownGrid>

        {/* ── KPI row ───────────────────────────────────────────────── */}
        <Col span={3}>
          <CrownMetricCard
            label="Enrollment"
            value={loading ? '…' : `${enr.current} / ${enr.target}`}
            hint={`${enrollPct}% of target`}
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Retention Rate"
            value={loading ? '…' : `${enr.retention_pct}%`}
            hint="Year-over-year"
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Collection Rate"
            value={loading ? '…' : `${fin.collection_pct}%`}
            hint="Tuition collected"
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Aid Awarded"
            value={loading ? '…' : fmt$(fin.aid_awarded)}
            hint="Current year"
          />
        </Col>

        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Mission & Finance">
        <CrownGrid>

        {/* ── Mission & culture ─────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Mission &amp; Culture">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow
                  label="Community survey pulse"
                  value={`${mis.survey_pulse_avg} / 5.0`}
                  sub="avg rating"
                />
                <StatRow
                  label="Service hours YTD"
                  value={mis.service_hours_ytd.toLocaleString()}
                  sub="hours logged"
                />
                <StatRow
                  label="Chapel attendance"
                  value={`${mis.chapel_attendance_pct}%`}
                  sub="of enrolled"
                />
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Finance health ────────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Finance Health">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Tuition billed"    value={fmt$(fin.tuition_billed)} />
                <StatRow label="Tuition collected"  value={fmt$(fin.tuition_collected)} sub={`${fin.collection_pct}%`} />
                <StatRow label="Aid awarded"        value={fmt$(fin.aid_awarded)} />
                <StatRow label="AR 90+ days"        value={fmt$(fin.ar_90_plus)} sub="overdue" />
              </tbody>
            </table>
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--crown-muted)', marginBottom: 2 }}>
                <span>Collection progress</span>
                <span>{fin.collection_pct}%</span>
              </div>
              <ProgressBar pct={fin.collection_pct} color="var(--crown-ok)" />
            </div>
          </CrownCard>
        </Col>

        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Enrollment & Compliance">
        <CrownGrid>

        {/* ── Enrollment trend ──────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Enrollment Trend">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Currently enrolled" value={enr.current}         sub="students" />
                <StatRow label="Enrollment target"  value={enr.target}          sub="seats" />
                <StatRow label="Waitlist"            value={enr.waitlist}        sub="pending" />
                <StatRow label="Retention rate"      value={`${enr.retention_pct}%`} sub="YoY" />
              </tbody>
            </table>
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--crown-muted)', marginBottom: 2 }}>
                <span>Enrolled vs target</span>
                <span>{enrollPct}%</span>
              </div>
              <ProgressBar pct={enrollPct} color={enrollPct >= 90 ? 'var(--crown-ok)' : enrollPct >= 75 ? 'var(--crown-warn)' : 'var(--crown-danger)'} />
            </div>
          </CrownCard>
        </Col>

        {/* ── Compliance & risk ─────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard
            title="Compliance &amp; Risk"
            right={<Pill color="green">{comp.required_checks_passing} checks passing</Pill>}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Safety incidents YTD"     value={comp.safety_incidents_ytd}  sub="reported" />
                <StatRow label="Audit log entries (30d)"  value={comp.audit_log_entries_30d.toLocaleString()} />
                <StatRow label="Branch protection checks" value={comp.required_checks_passing} sub="enforced" />
              </tbody>
            </table>
            <div style={{ marginTop: 12 }}>
              <a
                href="/integrity"
                style={{ fontSize: 12, color: 'var(--crown-brand)', textDecoration: 'none', fontWeight: 600 }}
              >
                View live system integrity →
              </a>
            </div>
          </CrownCard>
        </Col>

        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
