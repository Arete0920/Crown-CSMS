import { useState, useEffect } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection   from '../components/layout/DashboardSection.jsx';
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
  meals_served_today:      287,
  free_reduced_count:       62,
  inventory_low_items:       4,
  payments_pending_count:   18,
  menu_today: [
    { item: 'Grilled Chicken Sandwich', category: 'Entree',    allergens: 'Gluten' },
    { item: 'Caesar Salad',             category: 'Side',      allergens: 'Dairy, Egg' },
    { item: 'Apple Slices',             category: 'Fruit',     allergens: 'None' },
    { item: 'Chocolate Milk',           category: 'Beverage',  allergens: 'Dairy' },
  ],
  menu_tomorrow: [
    { item: 'Beef Tacos',           category: 'Entree',   allergens: 'Gluten, Dairy' },
    { item: 'Corn',                 category: 'Side',     allergens: 'None' },
    { item: 'Orange Wedges',        category: 'Fruit',    allergens: 'None' },
    { item: '2% White Milk',        category: 'Beverage', allergens: 'Dairy' },
  ],
  inventory_low: [
    { item: 'Whole wheat buns',  stock: '2 cases',   reorder_level: '5 cases',  severity: 'red'    },
    { item: 'Chocolate milk',    stock: '48 units',  reorder_level: '72 units', severity: 'yellow' },
    { item: 'Apple sauce cups',  stock: '24 units',  reorder_level: '48 units', severity: 'yellow' },
    { item: 'Latex gloves (M)',  stock: '1 box',     reorder_level: '3 boxes',  severity: 'red'    },
  ],
  participation_trend: [
    { label: 'Mon',  count: 274 },
    { label: 'Tue',  count: 281 },
    { label: 'Wed',  count: 290 },
    { label: 'Thu',  count: 287 },
  ],
  alerts: [
    { label: '2 inventory items critically low  reorder immediately',        severity: 'red'    },
    { label: '18 unpaid lunch balances  $342 aggregate outstanding',         severity: 'yellow' },
    { label: 'Free/reduced verification renewals due for 8 students (April)', severity: 'yellow' },
    { label: 'Chocolate milk deliverya delayed  contact vendor',             severity: 'gray'   },
  ],
};

async function fetchFoodMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/food/metrics/`;
  const headers = { Accept: 'application/json' };
  if (token)    headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id']   = schoolId;
  try {
    const res = await globalThis.fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: DEMO };
  }
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

/*  Food / Lunch Program KPI flip cards  */
const ADMIN_KPI = [
  { label: "Meals Today",         value: "312",     trend: null,             trendUp: null,
    definition: "Total meals served today across all meal periods (breakfast, lunch, aftercare).",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Free/Reduced %",      value: "28%",     trend: null,             trendUp: null,
    definition: "Percentage of students participating in federal free or reduced-price meal programs.",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Low Balance Alerts",  value: "12",      trend: "+3 vs yesterday",trendUp: false,
    definition: "Student accounts with a meal balance below $5.00  contact families.",
    dataSource: "Food Module", dataHref: "/food" },
  { label: "Revenue Today",       value: "$1,248",  trend: null,             trendUp: null,
    definition: "Total meal revenue collected today (paid accounts only, excluding free/reduced).",
    dataSource: "Food Module", dataHref: "/food" },
];
export default function FoodDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: DEMO });

  useEffect(() => {
    fetchFoodMetrics().then(({ ok, data }) => {
      setState({ loading: false, live: ok, data });
    });
  }, []);

  const { loading, live, data } = state;
  const alerts    = data.alerts              || DEMO.alerts;
  const menuToday = data.menu_today          || DEMO.menu_today;
  const menuTmrw  = data.menu_tomorrow       || DEMO.menu_tomorrow;
  const invLow    = data.inventory_low       || DEMO.inventory_low;
  const trend     = data.participation_trend || DEMO.participation_trend;
  const maxTrend  = Math.max(...trend.map(t => t.count), 1);

  return (
    <CrownLayout
      title="Food Services"
      subtitle="Meals, inventory, participation, and payment tracking"
      right={<Pill color={live ? 'green' : 'gray'}>{live ? 'LIVE' : 'DEMO'}</Pill>}
    >
      <KpiStrip cards={ADMIN_KPI} />
      {loading && <p style={{ color: 'var(--crown-muted)', padding: 16 }}>Loading</p>}

      <DashboardSection title="Overview">
        <CrownGrid>
          <Col span={3}><CrownMetricCard label="Meals Served Today" value={data.meals_served_today ?? DEMO.meals_served_today} /></Col>
          <Col span={3}><CrownMetricCard label="Free / Reduced Students" value={data.free_reduced_count ?? DEMO.free_reduced_count} /></Col>
          <Col span={3}><CrownMetricCard label="Low Inventory Items" value={data.inventory_low_items ?? DEMO.inventory_low_items} /></Col>
          <Col span={3}><CrownMetricCard label="Payments Pending" value={data.payments_pending_count ?? DEMO.payments_pending_count} /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Menu &amp; Inventory">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Menu  Today &amp; Tomorrow">
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--crown-muted)', marginBottom: 6 }}>TODAY</div>
                {menuToday.map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--crown-border)', fontSize: 13 }}>
                    <span style={{ fontWeight: 500, color: 'var(--crown-ink)' }}>{m.item}</span>
                    <span style={{ color: 'var(--crown-muted)', fontSize: 11 }}>{m.allergens !== 'None' ? ` ${m.allergens}` : ''}</span>
                  </div>
                ))}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--crown-muted)', marginBottom: 6 }}>TOMORROW</div>
                {menuTmrw.map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--crown-border)', fontSize: 13 }}>
                    <span style={{ fontWeight: 500, color: 'var(--crown-ink)' }}>{m.item}</span>
                    <span style={{ color: 'var(--crown-muted)', fontSize: 11 }}>{m.allergens !== 'None' ? ` ${m.allergens}` : ''}</span>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Inventory  Low Stock">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {invLow.map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 12px', borderRadius: 6,
                    background: item.severity === 'red' ? 'var(--crown-danger-bg)' : 'var(--crown-warn-bg)',
                    border: '1px solid var(--crown-border)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--crown-ink)' }}>{item.item}</div>
                      <div style={{ fontSize: 11, color: 'var(--crown-muted)' }}>Stock: {item.stock} (reorder at {item.reorder_level})</div>
                    </div>
                    <Pill color={item.severity}>{item.severity === 'red' ? 'CRITICAL' : 'LOW'}</Pill>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Participation &amp; Alerts">
        <CrownGrid>
          <Col span={6}>
            <CrownCard title="Participation Trend (This Week)">
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, height: 80, padding: '0 8px' }}>
                {trend.map((t, i) => (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <div style={{ fontSize: 11, color: 'var(--crown-ink)', fontWeight: 600 }}>{t.count}</div>
                    <div style={{ width: '100%', background: 'var(--crown-brand)', borderRadius: '3px 3px 0 0', height: `${Math.round((t.count / maxTrend) * 60)}px` }} />
                    <div style={{ fontSize: 11, color: 'var(--crown-muted)' }}>{t.label}</div>
                  </div>
                ))}
              </div>
            </CrownCard>
          </Col>
          <Col span={6}>
            <CrownCard title="Alerts">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {alerts.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 6,
                    background: a.severity === 'red' ? 'var(--crown-danger-bg)' : a.severity === 'yellow' ? 'var(--crown-warn-bg)' : 'var(--crown-surface-2)',
                    border: '1px solid var(--crown-border)' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      background: a.severity === 'red' ? 'var(--crown-danger)' : a.severity === 'yellow' ? 'var(--crown-warn)' : 'var(--crown-muted)' }} />
                    <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{a.label}</span>
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
