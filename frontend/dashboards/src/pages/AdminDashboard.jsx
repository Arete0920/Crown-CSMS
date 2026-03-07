import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import { authenticatedFetch } from '../utils/authClient.js';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import FlipWidget from '../components/dashboard/FlipWidget.jsx';
import FeedWidget from '../components/dashboard/FeedWidget.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

/* ── Auth helpers ──────────────────────────────────────────────────────── */
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

async function fetchAdminMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/admin/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: null };
  }
}

/* ── Demo data for sections not yet backed by live API ──────────────── */
const DEMO_THREADS = [
  { from: 'Mrs. Johnson (Teacher)',    subject: 'Field trip permission slips needed', ago: '2h ago'    },
  { from: 'Parent: Williams, T.',      subject: 'RE: Attendance concern — 3/4 absences', ago: '4h ago' },
  { from: 'Coach Davis',               subject: 'Spring sports practice schedule',       ago: 'Yesterday'},
  { from: 'Admin Office',              subject: 'Parent volunteer sign-up deadline',     ago: 'Yesterday'},
  { from: 'Parent: Chen, R.',          subject: 'Grade inquiry — Math 301 retake',       ago: '2d ago'  },
];

const DEMO_EVENTS = [
  { name: 'Morning Chapel',         date: 'Today, 9:00 AM'  },
  { name: 'Board Meeting',          date: 'Thu, 6:00 PM'    },
  { name: 'Spring Concert',         date: 'Fri, 7:00 PM'    },
  { name: 'Quarter End / Grading',  date: 'Mar 14'          },
  { name: 'Parent Conference Day',  date: 'Mar 21'          },
];

const DEMO_DEVOTION = {
  verse:     '"For I know the plans I have for you," declares the Lord, "plans to prosper you and not to harm you, plans to give you hope and a future."',
  reference: 'Jeremiah 29:11 (NIV)',
  reflection:'Lead your school today with the confidence that comes from knowing your work is guided by something greater. Every interaction is an opportunity to build hope.',
  prayer:    'Lord, guide our decisions today. May this community reflect Your love in every classroom, hallway, and conversation. Amen.',
};

/* ── Pill ────────────────────────────────────────────────────────────── */
const PILL_COLORS = {
  red:    { background: 'var(--crown-danger-bg)', color: 'var(--crown-danger)', border: 'var(--crown-danger)' },
  yellow: { background: 'var(--crown-warn-bg)',   color: 'var(--crown-warn)',   border: 'var(--crown-warn)'   },
  green:  { background: 'var(--crown-ok-bg)',     color: 'var(--crown-ok)',     border: 'var(--crown-ok)'     },
  gray:   { background: 'var(--crown-surface-2)', color: 'var(--crown-muted)', border: 'var(--crown-border)'  },
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

/* ── Funnel step ─────────────────────────────────────────────────────── */
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
      {!isLast && (
        <span style={{ fontSize: 16, color: 'var(--crown-muted)', flexShrink: 0 }}>→</span>
      )}
    </div>
  );
}

/* ── Quick action link ───────────────────────────────────────────────── */
function QuickAction({ href, label, icon }) {
  return (
    <a
      href={href}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '9px 12px', borderRadius: 8,
        background: 'var(--crown-surface-2)', border: '1px solid var(--crown-border)',
        color: 'var(--crown-ink)', textDecoration: 'none', fontSize: 13, fontWeight: 600,
        transition: 'border-color 150ms, background 150ms',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--crown-gold)'; e.currentTarget.style.background = 'var(--crown-surface)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--crown-border)'; e.currentTarget.style.background = 'var(--crown-surface-2)'; }}
    >
      {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
      {label}
      <span style={{ marginLeft: 'auto', color: 'var(--crown-gold)', fontWeight: 800 }}>→</span>
    </a>
  );
}

/* ── Executive insight metric tile ──────────────────────────────────── */
function ExecMetric({ label, value, hint }) {
  return (
    <div style={{
      flex: '1 1 180px', minWidth: 160,
      background: 'var(--crown-surface-2)', border: '1px solid var(--crown-border)',
      borderRadius: 8, padding: '12px 16px',
    }}>
      <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--crown-ink)', marginBottom: 2 }}>{value}</div>
      {hint && <div style={{ fontSize: 11, color: 'var(--crown-muted)' }}>{hint}</div>}
    </div>
  );
}

/* ── Devotion card content ───────────────────────────────────────────── */
function DevotionCard({ devotion }) {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 11, color: 'var(--crown-gold)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8 }}>
        {today}
      </div>
      <blockquote style={{
        margin: 0, padding: '10px 14px',
        background: 'var(--crown-surface-2)', borderLeft: `3px solid var(--crown-gold)`,
        borderRadius: '0 8px 8px 0', fontSize: 13, fontStyle: 'italic', color: 'var(--crown-ink)',
        lineHeight: 1.6,
      }}>
        {devotion.verse}
        <footer style={{ fontSize: 11, color: 'var(--crown-gold)', fontStyle: 'normal', fontWeight: 700, marginTop: 6 }}>
          — {devotion.reference}
        </footer>
      </blockquote>
      <div style={{ fontSize: 13, color: 'var(--crown-muted)', lineHeight: 1.6 }}>
        <strong style={{ color: 'var(--crown-ink)', display: 'block', marginBottom: 4 }}>Reflection</strong>
        {devotion.reflection}
      </div>
      <div style={{
        fontSize: 12, color: 'var(--crown-muted)', lineHeight: 1.6,
        padding: '8px 12px', background: 'var(--crown-surface-2)', borderRadius: 8,
        border: '1px solid var(--crown-border)',
      }}>
        <strong style={{ color: 'var(--crown-ink)', display: 'block', marginBottom: 2 }}>Prayer</strong>
        {devotion.prayer}
      </div>
    </div>
  );
}

/* ── Main component ─────────────────────────────────────────────────── */
/* â”€â”€ Head-of-School KPI flip cards (blue front, gold back) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
const ADMIN_KPI = [
  { label: "Enrollment",        value: "742/760", trend: "+4.1% vs goal",   trendUp: true,
    definition: "Total active students enrolled this term vs. capacity. Click Enrollment for drill-down by grade.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
  { label: "Yield Rate",        value: "91%",     trend: "+4.9% vs last yr", trendUp: true,
    definition: "Percentage of accepted applicants who enrolled. Driven by admissions funnel conversion.",
    dataSource: "Admissions Pipeline", dataHref: "/admissions" },
  { label: "Attendance Today",  value: "96.4%",   trend: "+0.8%",            trendUp: true,
    definition: "Percentage of enrolled students marked present today across all sections.",
    dataSource: "Attendance Module", dataHref: "/attendance" },
  { label: "Tuition Collected", value: "93.1%",   trend: "+6.0% vs last yr", trendUp: true,
    definition: "Percentage of billed tuition that has been collected as of today across all active households.",
    dataSource: "Billing Module", dataHref: "/billing" },
  { label: "Financial Aid Used", value: "68%",    trend: "-2.3%",            trendUp: false,
    definition: "Portion of the annual aid budget that has been awarded to students this term.",
    dataSource: "Financial Aid Module", dataHref: "/financial-aid" },
  { label: "Attrition",         value: "8%",      trend: "-1.6% vs last yr", trendUp: true,
    definition: "Percentage of enrolled students who withdrew during this academic year.",
    dataSource: "Enrollment Module", dataHref: "/admissions" },
];
export default function AdminDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: null });
  const [metricsError, setMetricsError] = useState('');
  const [exec, setExec] = useState(null);
  const [execError, setExecError] = useState('');

  useEffect(() => {
    fetchAdminMetrics().then(({ ok, data }) => {
      if (!ok || !data) setMetricsError('Admin metrics unavailable — API error');
      setState({ loading: false, live: ok && !!data, data });
    });
  }, []);

  useEffect(() => {
    authenticatedFetch('/api/executive360/me/overview/')
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => {
        setExec(d && d.available ? d : null);
      })
      .catch((err) => {
        const msg = err?.message ?? typeof err === 'string' ? err : 'Unknown error';
        setExecError(`Executive insights unavailable — ${msg}`);
      });
  }, []);

  const { loading, live, data } = state;
  const f      = data?.enrollment_funnel    || {};
  const alerts = data?.operational_alerts   || [];

  /* ── Build FlipWidget payload from live alert data ── */
  const flipWidget = {
    title:    'Operational Health',
    subtitle: 'Today at a glance',
    data: {
      front: {
        good: alerts.filter(a => a.count === 0).length,
        warn: alerts.filter(a => a.count > 0 && a.count <= 3).length,
        bad:  alerts.filter(a => a.count > 3).length,
      },
      back: {
        items: alerts.map(a => ({
          text:  `${a.label}: ${a.count}`,
          level: a.count === 0 ? 'good' : a.count <= 3 ? 'warn' : 'bad',
        })),
      },
    },
  };

  /* ── Feed widget payloads ── */
  const commWidget = {
    title:    'Communications',
    subtitle: 'Recent messages',
    data: { threads: DEMO_THREADS },
  };
  const calWidget = {
    title:    'Upcoming Events',
    subtitle: 'School calendar',
    data: {
      items: DEMO_EVENTS.map(e => ({
        from:    e.name,
        subject: e.date,
      })),
    },
  };

  return (
    <CrownLayout title="Administration" subtitle="Principal & operations command center">
      <KpiStrip cards={ADMIN_KPI} />
      <ErrorBanner title="Dashboard unavailable" message={metricsError} />

      {!data && !metricsError && (
        <div style={{ opacity: 0.6, padding: 24 }}>Loading dashboard…</div>
      )}

      {/* ══════════════════════════════════════════════════
          ROW 1 — KPI TILES
      ══════════════════════════════════════════════════ */}
      {data && (
      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}>
            <CrownMetricCard
              label="Enrolled"
              value={loading ? '…' : String(data.enrolled ?? '—')}
              hint="Active students"
            />
          </Col>
          <Col span={3}>
            <CrownMetricCard
              label="Attendance Flags"
              value={loading ? '…' : String(data.attendance_flags_today ?? '—')}
              hint="Today"
            />
          </Col>
          <Col span={3}>
            <CrownMetricCard
              label="Discipline"
              value={loading ? '…' : String(data.discipline_incidents_week ?? '—')}
              hint="Incidents this week"
            />
          </Col>
          <Col span={3}>
            <CrownMetricCard
              label="Messages Pending"
              value={loading ? '…' : String(data.messages_pending ?? '—')}
              hint="Awaiting reply"
            />
          </Col>
        </CrownGrid>
      </DashboardSection>
      )}

      {/* ══════════════════════════════════════════════════
          ROW 2 — ALERTS / ACTION ITEMS
      ══════════════════════════════════════════════════ */}
      {data && (
      <DashboardSection title="Operations">
        <CrownGrid>

          {/* Flip Card — Operational Health */}
          <Col span={3}>
            <FlipWidget widget={flipWidget} />
          </Col>

          {/* Enrollment Funnel */}
          <Col span={3}>
            <CrownCard
              title="Enrollment Funnel"
              right={<Pill color="gray">Current year</Pill>}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
                <FunnelStep label="Inquiries"  value={f.inquiries}  />
                <FunnelStep label="Applicants" value={f.applicants} />
                <FunnelStep label="Admitted"   value={f.admitted}   />
                <FunnelStep label="Enrolled"   value={f.enrolled}   isLast />
              </div>
              <div style={{ marginTop: 12, fontSize: 11, color: 'var(--crown-muted)' }}>
                Inquiry-to-enrolled conversion:{' '}
                <strong style={{ color: 'var(--crown-ink)' }}>
                  {f.inquiries ? Math.round((f.enrolled / f.inquiries) * 100) : '—'}%
                </strong>
              </div>
            </CrownCard>
          </Col>

          {/* Operational Alerts */}
          <Col span={3}>
            <CrownCard
              title="Operational Alerts"
              right={
                <Pill color={alerts.some(a => a.count > 0) ? 'red' : 'green'}>
                  {alerts.filter(a => a.count > 0).length} active
                </Pill>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                {alerts.map((a) => (
                  <div
                    key={a.type}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '7px 10px', borderRadius: 6,
                      background: a.count === 0 ? 'var(--crown-ok-bg)' : a.count <= 3 ? 'var(--crown-warn-bg)' : 'var(--crown-danger-bg)',
                      border: `1px solid ${a.count === 0 ? 'var(--crown-ok)' : a.count <= 3 ? 'var(--crown-warn)' : 'var(--crown-danger)'}`,
                    }}
                  >
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                    <span style={{ fontWeight: 800, fontSize: 14, color: a.count === 0 ? 'var(--crown-ok)' : a.count <= 3 ? 'var(--crown-warn)' : 'var(--crown-danger)' }}>
                      {a.count}
                    </span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>

          {/* Quick Actions */}
          <Col span={3}>
            <CrownCard title="Quick Actions">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                <QuickAction href="/communications"  label="Compose announcement"  icon="📢" />
                <QuickAction href="/discipline"      label="Open incident report"   icon="📋" />
                <QuickAction href="/financial-aid"   label="Review aid queue"       icon="💰" />
                <QuickAction href="/admissions"      label="Admissions pipeline"    icon="🎓" />
                <QuickAction href="/hr"              label="Human Resources"        icon="👥" />
                <QuickAction href="/safety"          label="Safety incidents"       icon="🛡️" />
                <QuickAction href="/wizards"         label="Wizard Hub"             icon="⚙️" />
              </div>
            </CrownCard>
          </Col>

        </CrownGrid>
      </DashboardSection>
      )}

      {/* ══════════════════════════════════════════════════
          ROW 3 — COMMUNICATIONS, CALENDAR & DEVOTION
      ══════════════════════════════════════════════════ */}
      <DashboardSection title="Communications & Spirit">
        <CrownGrid>

          {/* Communications Feed */}
          <Col span={4}>
            <FeedWidget widget={commWidget} onExpand={() => window.location.href = '/communications'} />
          </Col>

          {/* Upcoming Events / Calendar */}
          <Col span={4}>
            <FeedWidget widget={calWidget} />
          </Col>

          {/* Devotion of the Day (Barnabas) */}
          <Col span={4}>
            <CrownCard
              title="Devotion of the Day"
              right={<span style={{ fontSize: 11, color: 'var(--crown-gold)', fontWeight: 700 }}>Barnabas</span>}
            >
              <DevotionCard devotion={DEMO_DEVOTION} />
            </CrownCard>
          </Col>

        </CrownGrid>
      </DashboardSection>

      {/* ══════════════════════════════════════════════════
          ROW 4 — EXECUTIVE INSIGHTS (TREND / METRICS)
      ══════════════════════════════════════════════════ */}
      <DashboardSection title="Executive Insights">
        <CrownGrid>
          <Col span={12}>
            <CrownCard
              title="Financial & Academic Snapshot"
              right={
                <Pill color={exec ? 'green' : 'gray'}>
                  {exec ? 'LIVE' : live ? 'DEMO' : 'NO DATA'}
                </Pill>
              }
            >
              {execError && <ErrorBanner title="Executive insights unavailable" message={execError} />}
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
                <ExecMetric
                  label="Receivables"
                  value={exec ? `$${(exec.receivables_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '$237,000'}
                  hint="Total billed across all households"
                />
                <ExecMetric
                  label="Aid Allocated"
                  value={exec ? `$${(exec.aid_allocated_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '$312,500'}
                  hint="Total awarded this year"
                />
                <ExecMetric
                  label="Academic Risk"
                  value={exec ? String(exec.at_risk_count ?? '—') : '12'}
                  hint="Students below 75% in any subject"
                />
                <ExecMetric
                  label="Overdue Work"
                  value={exec ? String(exec.missing_assignments_total ?? '—') : '47'}
                  hint="Assignments past due date"
                />
                {data && (
                  <ExecMetric
                    label="Billing Delinquencies"
                    value={loading ? '…' : String(data.billing_delinquencies ?? '—')}
                    hint="Accounts past due"
                  />
                )}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

    </CrownLayout>
  );
}
