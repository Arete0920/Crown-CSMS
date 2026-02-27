import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import { authenticatedFetch } from '../utils/authClient.js';

/* ── Auth helpers (matches existing Crown pattern) ─────────────────── */
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
    return { ok: false, data: null };   // no silent fallback — follow DEMO_MODE_POLICY
  }
}

/* ── Pill ────────────────────────────────────────────────────────────── */
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

/* ── Alert severity color ────────────────────────────────────────────── */
function alertColor(count) {
  if (count === 0) return 'green';
  if (count <= 3)  return 'yellow';
  return 'red';
}

/* ── Funnel step ─────────────────────────────────────────────────────── */
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
      {!isLast && (
        <span style={{ fontSize: 16, color: '#9ca3af', flexShrink: 0 }}>→</span>
      )}
    </div>
  );
}

/* ── Quick action link ───────────────────────────────────────────────── */
function QuickAction({ href, label }) {
  return (
    <a
      href={href}
      className="crown-btn"
      style={{ justifyContent: 'flex-start', marginBottom: 4, display: 'flex' }}
    >
      {label} →
    </a>
  );
}

/* ── Executive insight metric tile ──────────────────────────────────── */
function ExecMetric({ label, value, hint }) {
  return (
    <div style={{
      flex: '1 1 180px', minWidth: 160,
      background: '#f8fafc', border: '1px solid #e5e7eb',
      borderRadius: 8, padding: '12px 16px',
    }}>
      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 2 }}>{value}</div>
      {hint && <div style={{ fontSize: 11, color: '#9ca3af' }}>{hint}</div>}
    </div>
  );
}

/* ── Main component ─────────────────────────────────────────────────── */
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
        setExecError('');
      })
      .catch((err) => {
        setExec(null);
        const msg =
          err && err.message ? err.message :
          typeof err === 'string' ? err :
          'Unknown error';
        setExecError(`Executive insights unavailable — API error: ${msg}`);
      });
  }, []);

  const { loading, live, data } = state;
  const f = data?.enrollment_funnel || {};
  const alerts = data?.operational_alerts || [];

  return (
    <CrownLayout title="Administration" subtitle="Principal & operations command center">
      <ErrorBanner title="Dashboard unavailable" message={metricsError} />

      {!data && !metricsError && (
        <div style={{ opacity: 0.6, padding: 24 }}>Loading dashboard…</div>
      )}

      {data && (
      <CrownGrid>

        {/* ── KPI row ───────────────────────────────────────────────── */}
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

        {/* ── Enrollment funnel ─────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard
            title="Enrollment Funnel"
            right={<Pill color="gray">Current year</Pill>}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
              <FunnelStep label="Inquiries"   value={f.inquiries}  />
              <FunnelStep label="Applicants"  value={f.applicants} />
              <FunnelStep label="Admitted"    value={f.admitted}   />
              <FunnelStep label="Enrolled"    value={f.enrolled}   isLast />
            </div>
            <div style={{ marginTop: 12, fontSize: 11, color: '#9ca3af' }}>
              Inquiry-to-enrolled conversion:{' '}
              <strong style={{ color: '#374151' }}>
                {f.inquiries ? Math.round((f.enrolled / f.inquiries) * 100) : '—'}%
              </strong>
            </div>
          </CrownCard>
        </Col>

        {/* ── Today at a glance ─────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard
            title="Today at a Glance"
            right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <tbody>
                {[
                  ['Attendance flags',      data.attendance_flags_today,    alertColor(data.attendance_flags_today)],
                  ['Discipline incidents',  data.discipline_incidents_week,  alertColor(data.discipline_incidents_week)],
                  ['Messages pending',      data.messages_pending,           alertColor(data.messages_pending)],
                  ['Billing delinquencies', data.billing_delinquencies,      alertColor(data.billing_delinquencies)],
                ].map(([label, val, color]) => (
                  <tr key={label} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '8px 0', color: '#6b7280' }}>{label}</td>
                    <td style={{ padding: '8px 0', textAlign: 'right' }}>
                      <Pill color={color}>{val ?? '—'}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Operational alerts ────────────────────────────────────── */}
        <Col span={6}>
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
                    background: a.count === 0 ? '#f0fdf4' : a.count <= 3 ? '#fefce8' : '#fef2f2',
                    border: `1px solid ${a.count === 0 ? '#bbf7d0' : a.count <= 3 ? '#fde047' : '#fecaca'}`,
                  }}
                >
                  <span style={{ fontSize: 13, color: '#374151' }}>{a.label}</span>
                  <span style={{ fontWeight: 800, fontSize: 14, color: a.count === 0 ? '#166534' : a.count <= 3 ? '#854d0e' : '#991b1b' }}>
                    {a.count}
                  </span>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

        {/* ── Quick actions ─────────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Quick Actions">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
              <QuickAction href="/communications"  label="Compose announcement" />
              <QuickAction href="/discipline"      label="Open incident report"  />
              <QuickAction href="/financial-aid"   label="Review aid queue"      />
              <QuickAction href="/admissions"      label="Admissions pipeline"   />
              <QuickAction href="/hr"              label="Human Resources"       />
              <QuickAction href="/safety"          label="Safety incidents"      />
              <QuickAction href="/integrity"       label="System integrity"      />
              <QuickAction href="/wizards"         label="Wizard Hub"            />
            </div>
          </CrownCard>
        </Col>

        {/* ── Executive Insights ────────────────────────────────────── */}
        <Col span={12}>
          <CrownCard
            title="Executive Insights"
            right={
              <Pill color={exec ? 'green' : 'gray'}>
                {exec ? 'LIVE' : 'NO DATA'}
              </Pill>
            }
          >
            {execError ? (
              <ErrorBanner title="Executive insights unavailable" message={execError} />
            ) : null}
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
              <ExecMetric
                label="Receivables"
                value={exec ? `$${(exec.receivables_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                hint="Total billed across all households"
              />
              <ExecMetric
                label="Aid Allocated"
                value={exec ? `$${(exec.aid_allocated_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                hint="Total awarded this year"
              />
              <ExecMetric
                label="Academic Risk"
                value={exec ? String(exec.at_risk_count ?? '—') : '—'}
                hint="Students below 75% in any subject"
              />
              <ExecMetric
                label="Overdue Work"
                value={exec ? String(exec.missing_assignments_total ?? '—') : '—'}
                hint="Assignments past due date"
              />
            </div>
          </CrownCard>
        </Col>

      </CrownGrid>
      )}
    </CrownLayout>
  );
}
