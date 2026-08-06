import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

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
      globalThis.fetch(`${apiBase()}/api/v1/hr/metrics/`, { headers }),
      globalThis.fetch(`${apiBase()}/api/v1/hr/employees/`, { headers }),
    ]);
    if (!metricsRes.ok || !listRes.ok) throw new Error('non-ok');
    const metrics = await metricsRes.json();
    const employees = await listRes.json();
    return { ok: true, data: { ...metrics, employees: Array.isArray(employees) ? employees : (employees.results || []) } };
  } catch {
    return { ok: false, data: DEMO };
  }
}

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

/*  HR / Staff KPI flip cards  */
const ADMIN_KPI = [
  { label: "Staff Active",         value: "84",   trend: null,              trendUp: null,
    definition: "Total full-time and part-time staff with active employment records.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Open Positions",       value: "2",    trend: null,              trendUp: null,
    definition: "Approved positions currently posted or in search phase.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Retention Rate",       value: "94%",  trend: "+2% vs last yr",  trendUp: true,
    definition: "Percentage of employees who remained employed from the start of the school year to today.",
    dataSource: "HR Module", dataHref: "/human-resources" },
  { label: "Trainings Due",        value: "7",    trend: null,              trendUp: null,
    definition: "Required professional development trainings due within the next 30 days.",
    dataSource: "HR Module", dataHref: "/human-resources" },
];
export default function HumanResources() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchHRData().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;

  return (
    <CrownLayout title="Human Resources" subtitle="Staff directory &amp; workforce overview"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={4}><CrownMetricCard label="Total Staff"    value={data.total_employees}    /></Col>
          <Col span={4}><CrownMetricCard label="Active"          value={data.active_employees}   /></Col>
          <Col span={4}><CrownMetricCard label="Inactive"        value={data.inactive_employees} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Directory">
        <CrownGrid>
          <Col span={5}>
            <CrownCard title="Staff by Department">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Department</th>
                    <th style={{ textAlign: 'right', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.by_department || []).map((row, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{row.department || 'Unassigned'}</td>
                      <td style={{ padding: '6px 8px', textAlign: 'right', fontWeight: 600, color: 'var(--crown-ink)' }}>{row.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={7}>
            <CrownCard title="Staff Directory">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--crown-surface-2)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Role</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Department</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--crown-muted)', fontWeight: 600 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.employees || []).map((e, i) => (
                    <tr key={e.id || i} style={{ borderTop: '1px solid var(--crown-border)' }}>
                      <td style={{ padding: '6px 8px', fontWeight: 500, color: 'var(--crown-ink)' }}>{e.first_name} {e.last_name}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-ink)' }}>{e.role}</td>
                      <td style={{ padding: '6px 8px', color: 'var(--crown-muted)' }}>{e.department || ''}</td>
                      <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                        <Pill color={e.active ? 'green' : 'red'}>{e.active ? 'Active' : 'Inactive'}</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
