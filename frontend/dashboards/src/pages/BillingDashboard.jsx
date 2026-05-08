import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

/*
  Crown2026 ? Billing Dashboard (0101 UI)
  - Export Center for 0093?0096
  - Manual Record Payment (0102)
  - Open invoice lookup (0102)

  Explicit assumptions:
  - Frontend is served from same origin as API OR you have a proxy configured.
  - Auth is handled by browser session cookie (credentials included).
  - Tenant scoping enforced server-side; if missing school context, API returns 403.

  Note: This repo uses UUIDs for household/account/charge IDs.
*/

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

// Dev-mode regression guard: catch missing API_BASE before it breaks exports.
// Skip this warning under tests to avoid noisy stderr that obscures true failures.
if (import.meta.env.DEV && import.meta.env.MODE !== "test" && !API_BASE) {
  console.warn("?? BillingDashboard: API_BASE is empty. Exports will fail. Set VITE_API_BASE_URL in .env.local");
}

export default function BillingDashboard() {
  const config = getDashboardTemplate('billing');
  return <CrownDashboardTemplate config={config} roleKey="billing" />;
}

