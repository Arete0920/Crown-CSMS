import { useEffect, useState } from 'react';
import { authenticatedFetch } from '../utils/authClient.js';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

const API_BASE = (import.meta?.env?.VITE_API_BASE_URL || '').trim();

async function fetchParentOverview() {
  const res = await authenticatedFetch(`${API_BASE}/api/parent360/me/overview/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function fmtDollars(cents) {
  if (cents === null || cents === undefined) return '—';
  return `$${(cents / 100).toFixed(2)}`;
}

function fmtPct(n) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(1)}%`;
}

function AlertBanner({ alerts }) {
  if (!alerts?.length) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      {alerts.map((a, i) => (
        <div
          key={i}
          style={{
            background: '#fff3cd',
            border: '1px solid #ffc107',
            borderRadius: 6,
            padding: '7px 12px',
            marginBottom: 5,
            fontSize: '0.85rem',
          }}
        >
          ⚠ {a.message}
        </div>
      ))}
    </div>
  );
}

function ChildCard({ child }) {
  const avg = child.current_average !== null ? fmtPct(child.current_average) : '—';
  const gpa = child.gpa !== null ? String(child.gpa) : '—';
  const balance = child.financial?.available ? fmtDollars(child.financial.balance_cents) : '—';
  const svc = child.service_hours?.available
    ? `${Number(child.service_hours.completed).toFixed(1)} / ${child.service_hours.required} hrs`
    : '—';

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: 10,
        padding: '14px 16px',
        marginBottom: 12,
        background: '#fff',
      }}
    >
      <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: 8 }}>
        {child.first_name} {child.last_name}
        {child.grade_level ? (
          <span style={{ fontWeight: 400, color: '#6b7280', marginLeft: 8, fontSize: '0.85rem' }}>
            Grade {child.grade_level}
          </span>
        ) : null}
      </div>

      <AlertBanner alerts={child.alerts} />

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 10 }}>
        {[
          { label: 'Average', value: avg },
          { label: 'GPA (est.)', value: gpa },
          { label: 'Missing', value: String(child.missing_assignments) },
          { label: 'Balance', value: balance },
          { label: 'Service Hrs', value: svc },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{
              background: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              padding: '6px 12px',
              minWidth: 90,
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#6b7280', textTransform: 'uppercase' }}>{label}</div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{value}</div>
          </div>
        ))}
      </div>

      {child.upcoming_assignments?.length > 0 && (
        <div>
          <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: 4 }}>Upcoming</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.85rem' }}>
            {child.upcoming_assignments.map((a, i) => {
              const due = a.due_date ? new Date(a.due_date).toLocaleDateString() : '—';
              return (
                <li key={i} style={{ marginBottom: 2 }}>
                  {a.name} <span style={{ color: '#9ca3af' }}>· due {due}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function ParentDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchParentOverview()
      .then(setData)
      .catch((err) => {
        setError(`Dashboard unavailable — API error: ${err.message}`);
      });
  }, []);

  const hh = data?.household || {};
  const children = data?.children || [];
  const balance = hh.balance_cents !== undefined ? fmtDollars(hh.balance_cents) : '—';
  const childCount = data?.children_count ?? (data ? children.length : null);
  const missingTotal = data?.missing_assignments_total ?? 0;
  const upcomingTotal = data?.upcoming_assignments_total ?? 0;

  // Aggregate any child alerts for the top banner
  const allAlerts = children.flatMap((c) => c.alerts || []);

  return (
    <CrownLayout
      title="Parent Dashboard"
      subtitle={hh.name ? `${hh.name} · Family overview` : 'Family academics, finance, and alerts'}
    >
      <ErrorBanner title="Dashboard unavailable" message={error} />

      {!data && !error && (
        <div style={{ opacity: 0.6, padding: 24 }}>Loading dashboard…</div>
      )}

      {data && (
        <>
          {allAlerts.length > 0 && <AlertBanner alerts={allAlerts} />}

          <CrownGrid>
            <Col span={3}>
              <CrownMetricCard label="Household Balance" value={balance} hint="Open invoices" />
            </Col>
            <Col span={3}>
              <CrownMetricCard
                label="Children"
                value={childCount !== null ? String(childCount) : '—'}
                hint="Active students"
              />
            </Col>
            <Col span={3}>
              <CrownMetricCard
                label="Missing Assignments"
                value={String(missingTotal)}
                hint="Across all children"
              />
            </Col>
            <Col span={3}>
              <CrownMetricCard
                label="Upcoming"
                value={String(upcomingTotal)}
                hint="Due in 7 days"
              />
            </Col>

            <Col span={12}>
              <CrownCard title="Children">
                {children.length === 0 ? (
                  <div style={{ opacity: 0.65 }}>No active children linked to this household.</div>
                ) : (
                  children.map((child) => <ChildCard key={child.id} child={child} />)
                )}
              </CrownCard>
            </Col>

            <Col span={12}>
              <CrownCard title="Quick Links">
                <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <a className="crown-btn" href="/academics/parent-snapshot">Parent Snapshot</a>
                  <a className="crown-btn" href="/parent/attendance">Attendance</a>
                  <a className="crown-btn" href="/finance/invoices">Invoices</a>
                  <a className="crown-btn" href="/communications">Messages</a>
                </nav>
              </CrownCard>
            </Col>
          </CrownGrid>
        </>
      )}
    </CrownLayout>
  );
}
