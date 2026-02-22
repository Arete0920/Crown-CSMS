import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

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

/* ── Progress bar ────────────────────────────────────────────────────── */
function ProgressBar({ pct, color = '#10b981' }) {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div style={{ height: 6, background: '#e5e7eb', borderRadius: 3, overflow: 'hidden', marginTop: 4 }}>
      <div style={{ height: '100%', width: `${clamped}%`, background: color, borderRadius: 3, transition: 'width 0.4s' }} />
    </div>
  );
}

/* ── Aging bucket bar (visual weight by amount) ──────────────────────── */
function AgingBar({ amount, maxAmount }) {
  const pct = maxAmount ? (amount / maxAmount) * 100 : 0;
  return (
    <div style={{ height: 4, background: '#e5e7eb', borderRadius: 2, overflow: 'hidden', width: '100%', marginTop: 3 }}>
      <div style={{ height: '100%', width: `${pct}%`, background: '#3b82f6', borderRadius: 2 }} />
    </div>
  );
}

/* ── StatRow ─────────────────────────────────────────────────────────── */
function StatRow({ label, value, sub, highlight }) {
  return (
    <tr style={{ borderBottom: '1px solid #f3f4f6' }}>
      <td style={{ padding: '8px 0', color: '#6b7280', fontSize: 13 }}>{label}</td>
      <td style={{ padding: '8px 0', textAlign: 'right' }}>
        <span style={{ fontWeight: 700, color: highlight || '#111827', fontSize: 14 }}>{value}</span>
        {sub && <span style={{ marginLeft: 6, fontSize: 11, color: '#9ca3af' }}>{sub}</span>}
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
    <CrownLayout title="Finance" subtitle="Business office · AR · collections · financial aid">
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

        {/* ── AR Aging table ────────────────────────────────────────── */}
        <Col span={8}>
          <CrownCard
            title="AR Aging"
            right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '6px 0', textAlign: 'left',  color: '#6b7280', fontWeight: 600 }}>Bucket</th>
                  <th style={{ padding: '6px 0', textAlign: 'center', color: '#6b7280', fontWeight: 600 }}>Accounts</th>
                  <th style={{ padding: '6px 0', textAlign: 'right',  color: '#6b7280', fontWeight: 600 }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {aging.map((row, i) => (
                  <tr key={row.bucket} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '10px 0' }}>
                      <div style={{
                        fontSize: 13, fontWeight: 600,
                        color: i === aging.length - 1 ? '#dc2626' : '#374151',
                      }}>
                        {row.bucket}
                      </div>
                      <AgingBar amount={row.amount} maxAmount={maxAgingAmount} />
                    </td>
                    <td style={{ padding: '10px 0', textAlign: 'center', color: '#6b7280', fontSize: 13 }}>
                      {row.count}
                    </td>
                    <td style={{
                      padding: '10px 0', textAlign: 'right', fontWeight: 700,
                      color: i === aging.length - 1 ? '#dc2626' : '#111827',
                      fontSize: 14,
                    }}>
                      {fmt$(row.amount)}
                    </td>
                  </tr>
                ))}
                <tr>
                  <td style={{ padding: '10px 0', fontWeight: 700, color: '#374151' }}>Total</td>
                  <td style={{ padding: '10px 0', textAlign: 'center', fontWeight: 700, color: '#374151' }}>
                    {aging.reduce((s, b) => s + b.count, 0)}
                  </td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 800, fontSize: 15, color: '#111827' }}>
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
                      <span style={{ color: '#374151', textTransform: 'uppercase', fontWeight: 600, fontSize: 11 }}>
                        {method}
                      </span>
                      <span style={{ color: '#111827', fontWeight: 700 }}>{fmt$(amount)}</span>
                    </div>
                    <ProgressBar pct={pct} color="#6366f1" />
                    <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 1 }}>{pct}% of collected</div>
                  </div>
                );
              })}
            </div>
          </CrownCard>
        </Col>

        {/* ── Collections ───────────────────────────────────────────── */}
        <Col span={6}>
          <CrownCard title="Collections">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <StatRow label="Paid this week"  value={fmt$(coll.paid_this_week)} />
                <StatRow label="Paid this month"  value={fmt$(coll.paid_this_month)} />
                <StatRow label="Outstanding"      value={fmt$(coll.outstanding)}   highlight="#dc2626" />
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
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginBottom: 2 }}>
                <span>Budget utilization</span>
                <span>{aidPct}%</span>
              </div>
              <ProgressBar pct={aidPct} color={aidPct > 90 ? '#ef4444' : '#10b981'} />
            </div>
            <div style={{ marginTop: 10 }}>
              <a
                href="/financial-aid"
                style={{ fontSize: 12, color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}
              >
                Open Financial Aid dashboard →
              </a>
            </div>
          </CrownCard>
        </Col>

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
                    background: warn ? '#fef2f2' : '#f0fdf4',
                    border: `1px solid ${warn ? '#fecaca' : '#bbf7d0'}`,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: 24, fontWeight: 900, color: warn ? '#dc2626' : '#166534' }}>{value}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>
          </CrownCard>
        </Col>

      </CrownGrid>
    </CrownLayout>
  );
}
