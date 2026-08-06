import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return { token: sessionStorage.getItem('crown.jwt.access') || '', schoolId: sessionStorage.getItem('crown.school.id') || '' };
  } catch { return { token: '', schoolId: '' }; }
}

const DEMO = {
  books_checked_out: 248, overdue_items: 17, new_materials_this_month: 34, digital_resources_active: 6,
  snapshot_date: 'Feb 26, 2026',
  overdue_list: [
    { borrower_id: 'STU-0042', title: 'To Kill a Mockingbird',  due_date: 'Feb 1',  days_overdue: 25 },
    { borrower_id: 'STU-0317', title: 'The Odyssey',            due_date: 'Feb 8',  days_overdue: 18 },
    { borrower_id: 'STU-1120', title: 'Biology Textbook 10',    due_date: 'Feb 10', days_overdue: 16 },
    { borrower_id: 'STA-0012', title: 'Graphic Novel Compendium',due_date: 'Feb 15', days_overdue: 11 },
    { borrower_id: 'STU-0891', title: 'AP Chemistry Reference', due_date: 'Feb 18', days_overdue: 8  },
  ],
  collection_by_category: [
    { category: 'Fiction',           count: 4820, pct: 100 },
    { category: 'Non-Fiction',       count: 3200, pct: 66  },
    { category: 'Reference',         count: 1100, pct: 23  },
    { category: 'Periodicals',       count:  480, pct: 10  },
    { category: 'Digital/eBooks',    count:  312, pct: 6   },
  ],
  digital_resources: [
    { name: 'JSTOR Academic',   licenses: 150, usage_mtd: 89  },
    { name: 'Britannica School',licenses: 500, usage_mtd: 212 },
    { name: 'Sora (OverDrive)', licenses: 300, usage_mtd: 117 },
    { name: 'ProQuest K-12',    licenses: 100, usage_mtd: 43  },
  ],
  alerts: [
    { label: '17 overdue items  2 over 21 days, contact parents', severity: 'red'    },
    { label: 'Library shelving reorganization scheduled Feb 28',  severity: 'yellow' },
  ],
};

async function fetchLibraryMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/library/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch { return { ok: false, data: DEMO }; }
}

function Pill({ color = 'gray', children }) {
  const map = {
    red:    { bg: 'var(--crown-danger-bg)', fg: 'var(--crown-danger)'  },
    yellow: { bg: 'var(--crown-warn-bg)',   fg: 'var(--crown-warn)'    },
    green:  { bg: 'var(--crown-ok-bg)',     fg: 'var(--crown-ok)'      },
    gray:   { bg: 'var(--crown-surface-2)', fg: 'var(--crown-muted)'   },
  };
  const v = map[color] || map.gray;
  return (
    <span style={{ display: 'inline-block', padding: '2px 9px', fontSize: 11, fontWeight: 700,
      borderRadius: 999, background: v.bg, color: v.fg }}>{children}</span>
  );
}

const TH = { padding: '7px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--crown-muted)', fontSize: 12 };
const TD = { padding: '8px 10px', color: 'var(--crown-ink)', fontSize: 13, borderBottom: '1px solid var(--crown-border)' };

/*  Library KPI flip cards  */
const ADMIN_KPI = [
  { label: "Checked Out",        value: "87",  trend: null,              trendUp: null,
    definition: "Total items (books, media, equipment) currently checked out to students or staff.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "Overdue Returns",    value: "14",  trend: "+2 vs last wk",  trendUp: false,
    definition: "Items past their return date that have not been checked back in.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "New Acquisitions",   value: "6",   trend: null,              trendUp: null,
    definition: "New titles or items added to the collection catalog this month.",
    dataSource: "Library Module", dataHref: "/library" },
  { label: "Active Borrowers",   value: "54",  trend: null,              trendUp: null,
    definition: "Unique students and staff who have checked out at least one item this term.",
    dataSource: "Library Module", dataHref: "/library" },
];
export default function LibraryDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchLibraryMetrics().then(({ ok, data }) => setState({ loading: false, live: ok, data }));
  }, []);

  const { loading, live, data } = state;
  const overdueList   = data.overdue_list           || DEMO.overdue_list;
  const collection    = data.collection_by_category || DEMO.collection_by_category;
  const digital       = data.digital_resources      || DEMO.digital_resources;
  const alerts        = data.alerts                 || DEMO.alerts;
  const maxCount      = Math.max(...collection.map(c => c.count), 1);

  return (
    <CrownLayout
      title="Library / Media Center"
      subtitle={`Snapshot: ${data.snapshot_date || DEMO.snapshot_date}`}
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: '4px 0' }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Books Checked Out"          value={data.books_checked_out          ?? DEMO.books_checked_out}          /></Col>
          <Col span={3}><CrownMetricCard label="Overdue Items"              value={data.overdue_items               ?? DEMO.overdue_items}               /></Col>
          <Col span={3}><CrownMetricCard label="New Materials (This Month)" value={data.new_materials_this_month    ?? DEMO.new_materials_this_month}    /></Col>
          <Col span={3}><CrownMetricCard label="Digital Resources Active"   value={data.digital_resources_active   ?? DEMO.digital_resources_active}   /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Circulation & Overdue">
        <CrownGrid>
          <Col span={8}>
            <CrownCard title="Overdue Items (Staff View  Redacted)">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Borrower ID', 'Title', 'Due Date', 'Overdue'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {overdueList.map((item, i) => (
                    <tr key={i} style={{ background: item.days_overdue >= 14 ? 'var(--crown-danger-bg)' : '' }}>
                      <td style={TD}>{item.borrower_id}</td>
                      <td style={TD}>{item.title}</td>
                      <td style={{ ...TD, color: 'var(--crown-muted)' }}>{item.due_date}</td>
                      <td style={{ ...TD, color: item.days_overdue >= 14 ? 'var(--crown-danger)' : 'var(--crown-warn)', fontWeight: 700 }}>{item.days_overdue}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CrownCard>
          </Col>
          <Col span={4}>
            <CrownCard title="Alerts">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: a.severity === 'red' ? 'var(--crown-danger-bg)' : 'var(--crown-warn-bg)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: a.severity === 'red' ? 'var(--crown-danger)' : 'var(--crown-warn)' }} />
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Collection & Digital Resources">
        <CrownGrid>
          <Col span={5}>
            <CrownCard title="Collection by Category">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {collection.map((c, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                      <span style={{ color: 'var(--crown-ink)' }}>{c.category}</span>
                      <span style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{c.count.toLocaleString()}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--crown-surface-2)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--crown-border)' }}>
                      <div style={{ width: `${Math.round((c.count / maxCount) * 100)}%`, height: '100%', background: 'var(--crown-brand)', borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={7}>
            <CrownCard title="Digital Resources (MTD Usage)">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--crown-surface-2)' }}>
                  {['Resource', 'Licenses', 'Usage MTD'].map(h => <th key={h} style={TH}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {digital.map((r, i) => (
                    <tr key={i}>
                      <td style={TD}>{r.name}</td>
                      <td style={TD}>{r.licenses}</td>
                      <td style={{ ...TD, fontWeight: 600, color: 'var(--crown-ok)' }}>{r.usage_mtd}</td>
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
