import { useEffect, useState } from 'react';
import { authenticatedFetch } from '../utils/authClient.js';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

const API_BASE = (import.meta?.env?.VITE_API_BASE_URL || '').trim();

async function fetchSelf() {
  const res = await authenticatedFetch(`${API_BASE}/api/student360/me/overview/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function fmt(n, fallback = '—') {
  if (n === null || n === undefined) return fallback;
  return String(n);
}

function fmtPct(n) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(1)}%`;
}

function fmtDollars(cents) {
  if (cents === null || cents === undefined) return '—';
  return `$${(cents / 100).toFixed(2)}`;
}

function AlertBanner({ alerts }) {
  if (!alerts?.length) return null;
  return (
    <div style={{ marginBottom: 12 }}>
      {alerts.map((a, i) => (
        <div
          key={i}
          style={{
            background: a.severity === 'warning' ? '#fff3cd' : '#f8d7da',
            border: `1px solid ${a.severity === 'warning' ? '#ffc107' : '#f5c6cb'}`,
            borderRadius: 6,
            padding: '8px 12px',
            marginBottom: 6,
            fontSize: '0.875rem',
          }}
        >
          ⚠ {a.message}
        </div>
      ))}
    </div>
  );
}

function AssignmentRow({ a }) {
  const due = a.due_date ? new Date(a.due_date).toLocaleDateString() : '—';
  return (
    <tr>
      <td style={{ padding: '6px 8px' }}>{a.name}</td>
      <td style={{ padding: '6px 8px', color: '#6b7280' }}>{due}</td>
      <td style={{ padding: '6px 8px', color: '#6b7280' }}>{fmt(a.points_possible)}</td>
    </tr>
  );
}

export default function StudentDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSelf()
      .then(setData)
      .catch((err) => {
        setError(`Dashboard unavailable — API error: ${err.message}`);
      });
  }, []);

  const v2 = data?.dashboard_v2 || {};
  const student = data?.student || {};
  const alerts = v2.alerts || [];
  const upcoming = v2.upcoming_assignments || [];

  const gpa = fmt(v2.gpa !== undefined ? v2.gpa : null);
  const avg = v2.current_average !== null && v2.current_average !== undefined
    ? fmtPct(v2.current_average)
    : '—';
  const missing = fmt(v2.missing_assignments, '0');
  const serviceHrs = v2.service_hours?.approved_hours !== undefined
    ? `${Number(v2.service_hours.approved_hours).toFixed(1)} hrs`
    : '—';
  const balance = v2.financial?.balance_cents !== undefined
    ? fmtDollars(v2.financial.balance_cents)
    : '—';

  return (
    <CrownLayout
      title={student.name ? `${student.name} — Dashboard` : 'Student Dashboard'}
      subtitle={`Grade ${student.grade || '—'} · Today's snapshot`}
    >
      <ErrorBanner title="Dashboard unavailable" message={error} />

      {!data && !error && (
        <div style={{ opacity: 0.6, padding: 24 }}>Loading dashboard…</div>
      )}

      {data && (
        <>
          <AlertBanner alerts={alerts} />

          <CrownGrid>
            <Col span={3}><CrownMetricCard label="GPA (est.)" value={gpa} hint="4.0 scale proxy" /></Col>
            <Col span={3}><CrownMetricCard label="Current Average" value={avg} hint="Weighted grade avg" /></Col>
            <Col span={3}><CrownMetricCard label="Missing Work" value={missing} hint="Unsubmitted past-due" /></Col>
            <Col span={3}><CrownMetricCard label="Balance Due" value={balance} hint="Open invoices" /></Col>

            <Col span={8}>
              <CrownCard title="Upcoming Assignments">
                {upcoming.length === 0 ? (
                  <div style={{ opacity: 0.65 }}>No upcoming assignments in the next 7 days.</div>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left', color: '#6b7280' }}>
                        <th style={{ padding: '4px 8px' }}>Assignment</th>
                        <th style={{ padding: '4px 8px' }}>Due</th>
                        <th style={{ padding: '4px 8px' }}>Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {upcoming.map((a, i) => <AssignmentRow key={i} a={a} />)}
                    </tbody>
                  </table>
                )}
              </CrownCard>
            </Col>

            <Col span={4}>
              <CrownCard title="Service Hours">
                <p style={{ fontSize: '1.5rem', fontWeight: 700, margin: '4px 0' }}>{serviceHrs}</p>
                <p style={{ fontSize: '0.8rem', color: '#6b7280', margin: 0 }}>
                  {v2.service_hours?.pending_hours !== undefined
                    ? `${Number(v2.service_hours.pending_hours).toFixed(1)} hrs pending`
                    : 'Approved hours'}
                </p>
              </CrownCard>
            </Col>

            <Col span={12}>
              <CrownCard title="Quick Links">
                <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <a className="crown-btn" href="/gradebook">Gradebook</a>
                  <a className="crown-btn" href="/transcript">Transcript</a>
                  <a className="crown-btn" href="/academics/student-work">Student Work</a>
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

