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
  total_incidents:    14,
  open_incidents:      5,
  resolved_incidents:  9,
  critical_open:       1,
  by_severity: [
    { severity: 'low',      count: 2 },
    { severity: 'medium',   count: 2 },
    { severity: 'high',     count: 0 },
    { severity: 'critical', count: 1 },
  ],
  by_category: [
    { category: 'Slip/Fall',        count: 4 },
    { category: 'Medical',          count: 3 },
    { category: 'Behavioral',       count: 3 },
    { category: 'Property Damage',  count: 2 },
    { category: 'Security',         count: 2 },
  ],
  recent: [
    { id: '1', category: 'Behavioral',    severity: 'critical', description: 'Physical altercation — hallway B2', resolved: false,  created_at: '2026-02-22' },
    { id: '2', category: 'Medical',       severity: 'medium',   description: 'Allergic reaction at lunch',        resolved: false,  created_at: '2026-02-21' },
    { id: '3', category: 'Slip/Fall',     severity: 'low',      description: 'Student fell on wet stairs',        resolved: true,   created_at: '2026-02-20' },
    { id: '4', category: 'Security',      severity: 'medium',   description: 'Tailgate entry — side door',        resolved: false,  created_at: '2026-02-19' },
    { id: '5', category: 'Property Damage',severity: 'low',     description: 'Broken window — classroom 14',     resolved: true,   created_at: '2026-02-18' },
  ],
};

const SEV_COLOR = { low: '#16a34a', medium: '#ca8a04', high: '#dc2626', critical: '#7f1d1d' };
const SEV_BG    = { low: '#dcfce7', medium: '#fef9c3', high: '#fee2e2', critical: '#fecaca' };

async function fetchSafetyData() {
  const { token, schoolId } = getSession();
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const [metricsRes, listRes] = await Promise.all([
      fetch(`${apiBase()}/api/v1/safety/metrics/`, { headers }),
      fetch(`${apiBase()}/api/v1/safety/incidents/`, { headers }),
    ]);
    if (!metricsRes.ok || !listRes.ok) throw new Error('non-ok');
    const metrics = await metricsRes.json();
    const list = await listRes.json();
    return {
      ok: true,
      data: { ...metrics, recent: Array.isArray(list) ? list.slice(0, 10) : (list.results || []).slice(0, 10) },
    };
  } catch {
    return { ok: false, data: DEMO };
  }
}

function SevBadge({ v }) {
  return (
    <span style={{
      background: SEV_BG[v] || '#f3f4f6',
      color: SEV_COLOR[v] || '#374151',
      borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700,
    }}>
      {v}
    </span>
  );
}

export default function SafetyDashboard() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchSafetyData().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;

  return (
    <CrownLayout title="Safety" subtitle="Campus incident tracking &amp; resolution">
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}

      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Total Incidents"    value={data.total_incidents}    />
        <CrownMetricCard label="Open"               value={data.open_incidents}     />
        <CrownMetricCard label="Resolved"           value={data.resolved_incidents} />
        <CrownMetricCard label="Critical Open"      value={data.critical_open}      />
      </div>

      <CrownGrid>
        {/* By Severity */}
        <Col span={4}>
          <CrownCard title="Open by Severity">
            {(data.by_severity || []).map((row, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
                <SevBadge v={row.severity} />
                <span style={{ fontWeight: 700, fontSize: 15 }}>{row.count}</span>
              </div>
            ))}
          </CrownCard>
        </Col>

        {/* By Category */}
        <Col span={4}>
          <CrownCard title="Top Categories">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <tbody>
                {(data.by_category || []).map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px' }}>{row.category}</td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontWeight: 600 }}>{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* Recent Incidents */}
        <Col span={4}>
          <CrownCard title="Recent Incidents">
            {(data.recent || []).slice(0, 5).map((inc, i) => (
              <div key={inc.id || i} style={{ padding: '7px 0', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ fontWeight: 600, fontSize: 12 }}>{inc.category}</span>
                  <SevBadge v={inc.severity} />
                </div>
                <div style={{ fontSize: 12, color: '#4b5563', marginBottom: 3 }}>{inc.description}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af' }}>
                  <span>{inc.created_at ? String(inc.created_at).slice(0, 10) : ''}</span>
                  <span style={{ color: inc.resolved ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                    {inc.resolved ? '✓ Resolved' : '● Open'}
                  </span>
                </div>
              </div>
            ))}
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
