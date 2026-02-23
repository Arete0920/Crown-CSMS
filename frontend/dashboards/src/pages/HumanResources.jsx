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
  total_employees:  42,
  active_employees: 39,
  inactive_employees: 3,
  by_department: [
    { department: 'Academics',       count: 18 },
    { department: 'Administration',  count:  7 },
    { department: 'Student Services',count:  6 },
    { department: 'Facilities',      count:  5 },
    { department: 'Finance',         count:  4 },
    { department: 'Technology',      count:  2 },
  ],
  employees: [
    { id: '1', first_name: 'Jane',  last_name: 'Smith',  role: 'Head of School',      department: 'Administration', active: true },
    { id: '2', first_name: 'Mark',  last_name: 'Torres', role: 'Dean of Academics',   department: 'Academics',      active: true },
    { id: '3', first_name: 'Linda', last_name: 'Park',   role: 'Director of Finance', department: 'Finance',        active: true },
    { id: '4', first_name: 'Brian', last_name: 'Hayes',  role: 'IT Coordinator',      department: 'Technology',     active: true },
    { id: '5', first_name: 'Sara',  last_name: 'Cole',   role: 'Registrar',           department: 'Administration', active: false },
  ],
};

async function fetchHRData() {
  const { token, schoolId } = getSession();
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const [metricsRes, listRes] = await Promise.all([
      fetch(`${apiBase()}/api/v1/hr/metrics/`, { headers }),
      fetch(`${apiBase()}/api/v1/hr/employees/`, { headers }),
    ]);
    if (!metricsRes.ok || !listRes.ok) throw new Error('non-ok');
    const metrics = await metricsRes.json();
    const employees = await listRes.json();
    return { ok: true, data: { ...metrics, employees: Array.isArray(employees) ? employees : (employees.results || []) } };
  } catch {
    return { ok: false, data: DEMO };
  }
}

const DEPT_COLOR = {
  Academics: '#2563eb', Administration: '#7c3aed', Finance: '#16a34a',
  'Student Services': '#ca8a04', Facilities: '#dc2626', Technology: '#0891b2',
};

export default function HumanResources() {
  const [state, setState] = useState({ loading: true, data: DEMO });

  useEffect(() => {
    fetchHRData().then(({ ok, data }) => setState({ loading: false, data }));
  }, []);

  const { loading, data } = state;

  return (
    <CrownLayout title="Human Resources" subtitle="Staff directory &amp; workforce overview">
      {loading && <p style={{ color: '#6b7280', padding: '4px 0' }}>Loading…</p>}

      {/* KPI row */}
      <div className="crown-metrics-row">
        <CrownMetricCard label="Total Staff"    value={data.total_employees}    />
        <CrownMetricCard label="Active"          value={data.active_employees}   />
        <CrownMetricCard label="Inactive"        value={data.inactive_employees} />
      </div>

      <CrownGrid>
        {/* By Department */}
        <Col span={5}>
          <CrownCard title="Staff by Department">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Department</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Count</th>
                </tr>
              </thead>
              <tbody>
                {(data.by_department || []).map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px' }}>
                      <span style={{
                        display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
                        background: DEPT_COLOR[row.department] || '#9ca3af',
                        marginRight: 6, verticalAlign: 'middle',
                      }} />
                      {row.department || 'Unassigned'}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontWeight: 600 }}>{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>

        {/* Employee List */}
        <Col span={7}>
          <CrownCard title="Staff Directory">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Name</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Role</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Department</th>
                  <th style={{ textAlign: 'center', padding: '6px 8px', color: '#6b7280', fontWeight: 600 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {(data.employees || []).map((e, i) => (
                  <tr key={e.id || i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '6px 8px', fontWeight: 500 }}>{e.first_name} {e.last_name}</td>
                    <td style={{ padding: '6px 8px', color: '#374151' }}>{e.role}</td>
                    <td style={{ padding: '6px 8px', color: '#6b7280' }}>{e.department || '—'}</td>
                    <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                      <span style={{
                        background: e.active ? '#dcfce7' : '#fee2e2',
                        color: e.active ? '#16a34a' : '#dc2626',
                        borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700,
                      }}>
                        {e.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
