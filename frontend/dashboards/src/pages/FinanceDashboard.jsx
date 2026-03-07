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
  ar_outstanding:       237_000,
  collected_this_month: 184_500,
  aid_awarded:          312_500,
  payment_failures:     3,
  ar_aging: [
    { bucket: '0–30 days',  amount: 98_400, count: 42 },
    { bucket: '31–60 days', amount: 71_200, count: 28 },
    { bucket: '61–90 days', amount: 19_200, count: 9  },
    { bucket: '90+ days',   amount: 48_200, count: 17 },
  ],
  collections: {
    paid_this_week:  23_400,
    paid_this_month: 184_500,
    outstanding:     237_000,
    payment_methods: { ach: 112_000, card: 54_500, check: 18_000 },
  },
  financial_aid: {
    awarded:           312_500,
    budget:            380_000,
    pending_decisions: 8,
    avg_award:         3_906,
  },
  operational: { payment_failures: 3, refunds: 1, chargebacks: 0 },
};

/* ── Finance KPI flip cards ──────────────────────────────────────────── */
const FINANCE_KPI = [
  { label: "AR Outstanding",    value: "$237K",   trend: null,             trendUp: null,
    definition: "Total accounts receivable across all family balances currently due.",
    dataSource: "Finance Module", dataHref: "/finance" },
  { label: "Collected (Month)", value: "$184.5K", trend: null,             trendUp: null,
    definition: "Payments posted to student accounts in the current calendar month.",
    dataSource: "Finance Module", dataHref: "/finance" },
  { label: "Aid Awarded",       value: "$312.5K", trend: null,             trendUp: null,
    definition: "Financial aid awards applied to family balances for the current year.",
    dataSource: "Financial Aid Module", dataHref: "/financial-aid" },
  { label: "Payment Failures",  value: "3",       trend: "needs attention", trendUp: false,
    definition: "ACH, card, or check payments declined — require staff follow-up and re-processing.",
    dataSource: "Finance Module", dataHref: "/finance" },
];

async function fetchFinanceMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/finance/metrics/`;
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
  if (n == null) return '—';
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

/* ── Aging bucket bar (visual weight by amount) ──────────────────────── */
function AgingBar({ amount, maxAmount }) {
  const pct = maxAmount ? (amount / maxAmount) * 100 : 0;
  return (
    <div style={{ height: 4, background: 'var(--crown-border)', borderRadius: 2, overflow: 'hidden', width: '100%', marginTop: 3 }}>
      <div style={{ height: '100%', width: `${pct}%`, background: 'var(--crown-brand)', borderRadius: 2 }} />
    </div>
  );
}

/* ── StatRow ─────────────────────────────────────────────────────────── */
function StatRow({ label, value, sub, highlight }) {
  return (
    <tr style={{ borderBottom: '1px solid var(--crown-border)' }}>
      <td style={{ padding: '8px 0', color: 'var(--crown-muted)', fontSize: 13 }}>{label}</td>
      <td style={{ padding: '8px 0', textAlign: 'right' }}>
        <span style={{ fontWeight: 700, color: highlight || 'var(--crown-ink)', fontSize: 14 }}>{value}</span>
        {sub && <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--crown-muted)' }}>{sub}</span>}
      </td>
    </tr>
  );
}

/* ── Main component ─────────────────────────────────────────────────── */
export default function FinanceDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchFinanceMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const aging   = data.ar_aging       || DEMO.ar_aging;
  const coll    = data.collections    || DEMO.collections;
  const aid     = data.financial_aid  || DEMO.financial_aid;
  const ops     = data.operational    || DEMO.operational;
  const methods = coll.payment_methods || DEMO.collections.payment_methods;

  const maxAgingAmount = Math.max(...aging.map(b => b.amount), 1);
  const aidPct = aid.budget ? Math.round((aid.awarded / aid.budget) * 100) : 0;

  return (
    <CrownLayout title="Finance" subtitle="Business office · AR · collections · financial aid"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={FINANCE_KPI} />
      <DashboardSection title="Key Indicators">
        <CrownGrid>

        {/* ── KPI row ───────────────────────────────────────────────── */}
        <Col span={3}>
          <CrownMetricCard
            label="AR Outstanding"
            value={loading ? '…' : fmt$(data.ar_outstanding)}
            hint="Total receivable"
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Collected (Month)"
            value={loading ? '…' : fmt$(data.collected_this_month)}
            hint="Payments posted"
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Aid Awarded"
            value={loading ? '…' : fmt$(data.aid_awarded)}
            hint="Current year"
          />
        </Col>
        <Col span={3}>
          <CrownMetricCard
            label="Payment Failures"
            value={loading ? '…' : String(data.payment_failures ?? '—')}
            hint="Needs resolution"
          />
        </Col>

        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Accounts Receivable">
        <CrownGrid>

        {/* ── AR Aging table ────────────────────────────────────────── */}
        <Col span={8}>
          <CrownCard title="AR Aging">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--crown-border)' }}>
                  <th style={{ padding: '6px 0', textAlign: 'left',  color: 'var(--crown-muted)', fontWeight: 600 }}>Bucket</th>
                  <th style={{ padding: '6px 0', textAlign: 'center', color: 'var(--crown-muted)', fontWeight: 600 }}>Accounts</th>
                  <th style={{ padding: '6px 0', textAlign: 'right',  color: 'var(--crown-muted)', fontWeight: 600 }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {aging.map((row, i) => (
                  <tr key={row.bucket} style={{ borderBottom: '1px solid var(--crown-border)' }}>
                    <td style={{ padding: '10px 0' }}>
                      <div style={{
                        fontSize: 13, fontWeight: 600,
                        color: i === aging.length - 1 ? 'var(--crown-danger)' : 'var(--crown-ink)',
                      }}>
                        {row.bucket}
                      </div>
                      <AgingBar amount={row.amount} maxAmount={maxAgingAmount} />
                    </td>
                    <td style={{ padding: '10px 0', textAlign: 'center', color: 'var(--crown-muted)', fontSize: 13 }}>
                      {row.count}
                    </td>
                    <td style={{
                      padding: '10px 0', textAlign: 'right', fontWeight: 700,
                      color: i === aging.length - 1 ? 'var(--crown-danger)' : 'var(--crown-ink)',
                      fontSize: 14,
                    }}>
                      {fmt$(row.amount)}
                    </td>
                  </tr>
                ))}
                <tr>
                  <td style={{ padding: '10px 0', fontWeight: 700, color: 'var(--crown-ink)' }}>Total</td>
                  <td style={{ padding: '10px 0', textAlign: 'center', fontWeight: 700, color: 'var(--crown-ink)' }}>
                    {aging.reduce((s, b) => s + b.count, 0)}
                  </td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 800, fontSize: 15, color: 'var(--crown-ink)' }}>
                    {fmt$(aging.reduce((s, b) => s + b.amount, 0))}
                  </td>
                </tr>
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Payment method mix ────────────────────────────────────── */}
        <Col span={4}>
          <CrownCard title="Payment Methods">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4 }}>
              {Object.entries(methods).map(([method, amount]) => {
                const total = Object.values(methods).reduce((s, v) => s + v, 0);
                const pct   = total ? Math.round((amount / total) * 100) : 0;
                return (
                  <div key={method}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
                      <span style={{ color: 'var(--crown-ink)', textTransform: 'uppercase', fontWeight: 600, fontSize: 11 }}>
                        {method}
                      </span>
                      <span style={{ color: 'var(--crown-ink)', fontWeight: 700 }}>{fmt$(amount)}</span>
                    </div>
                    <ProgressBar pct={pct} color="var(--crown-brand)" />
                    <div style={{ fontSize: 10, color: 'var(--crown-muted)', marginTop: 1 }}>{pct}% of collected</div>
                  </div>
                );
              })}
            </div>
          </CrownCard>
        </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Collections & Aid">
        <CrownGrid>
        {/* ── Collections ───────────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Collections">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Paid this week"  value={fmt$(coll.paid_this_week)} />
                <StatRow label="Paid this month"  value={fmt$(coll.paid_this_month)} />
                <StatRow label="Outstanding"      value={fmt$(coll.outstanding)}   highlight="var(--crown-danger)" />
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* ── Financial aid ─────────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard
            title="Financial Aid"
            right={<Pill color={aid.pending_decisions > 0 ? 'yellow' : 'green'}>{aid.pending_decisions} pending</Pill>}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Awarded this year"   value={fmt$(aid.awarded)} />
                <StatRow label="Budget"              value={fmt$(aid.budget)} />
                <StatRow label="Pending decisions"   value={String(aid.pending_decisions)} />
                <StatRow label="Average award"       value={fmt$(aid.avg_award)} sub="per family" />
              </tbody>
            </table>
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--crown-muted)', marginBottom: 2 }}>
                <span>Budget utilization</span>
                <span>{aidPct}%</span>
              </div>
              <ProgressBar pct={aidPct} color={aidPct > 90 ? 'var(--crown-danger)' : 'var(--crown-ok)'} />
            </div>
            <div style={{ marginTop: 10 }}>
              <a
                href="/financial-aid"
                style={{ fontSize: 12, color: 'var(--crown-brand)', textDecoration: 'none', fontWeight: 600 }}
              >
                Open Financial Aid dashboard →
              </a>
            </div>
          </CrownCard>
        </Col>

        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Operational">
        <CrownGrid>

        {/* ── Operational counters ──────────────────────────────────── */}
        <Col span={12}>
          <CrownCard title="Operational">
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 4 }}>
              {[
                { label: 'Payment failures', value: ops.payment_failures, warn: ops.payment_failures > 0 },
                { label: 'Refunds issued',   value: ops.refunds,          warn: false },
                { label: 'Chargebacks',      value: ops.chargebacks,      warn: ops.chargebacks > 0 },
              ].map(({ label, value, warn }) => (
                <div
                  key={label}
                  style={{
                    flex: '1 1 160px',
                    padding: '12px 16px',
                    borderRadius: 6,
                    background: warn ? 'var(--crown-danger-bg)' : 'var(--crown-ok-bg)',
                    border: `1px solid var(--crown-border)`,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: 24, fontWeight: 900, color: warn ? 'var(--crown-danger)' : 'var(--crown-ok)' }}>{value}</div>
                  <div style={{ fontSize: 12, color: 'var(--crown-muted)', marginTop: 2 }}>{label}</div>
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
