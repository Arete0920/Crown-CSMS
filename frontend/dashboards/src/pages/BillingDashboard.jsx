import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

/*
  CROWN ? Billing Dashboard (0101 UI)
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

// Dev-mode regression guard: exports use the configured API client, so a missing
// API base should not block the demo shell itself.
if (import.meta.env.DEV && import.meta.env.MODE !== "test" && !API_BASE) {
  console.info("BillingDashboard: using same-origin API base in development.");
}

export default function BillingDashboard() {
  const config = getDashboardTemplate('billing');
  return <CrownDashboardTemplate config={config} roleKey="billing" />;
}

