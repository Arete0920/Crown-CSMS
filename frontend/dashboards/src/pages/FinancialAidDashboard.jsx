import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

/**
 * Financial Aid reports may show canonical, school-scoped dashboard API facts.
 * The legacy page template also holds illustrative metrics, simulated activity,
 * and operational-looking statuses; none is valid live financial evidence.
 *
 * Keep the shared liveDataKey/API binding while withholding that illustrative
 * content in all environments, including when the API is unavailable. The
 * dashboard template's existing error and sample provenance handling remains
 * authoritative. No financial transaction is performed by this page.
 */
export function getFinancialAidDashboardConfig() {
  const template = getDashboardTemplate('financialAid');

  return {
    ...template,
    title: 'Financial Aid',
    eyebrow: 'CROWN Financial Aid',
    subtitle: 'School-scoped financial aid reporting',
    schoolName: null,
    updatesCount: null,
    user: { initials: 'FA', name: 'Financial Aid', role: 'Financial Aid' },
    metrics: [],
    priorities: [],
    alerts: [],
    commandModules: [],
    trendPanels: [],
    activities: [],
    statuses: [],
    communications: false,
    faithCommunity: false,
    quickActions: [
      { label: 'Open Financial Aid Setup', href: '/aid-setup' },
      { label: 'Open Finance', href: '/finance' },
    ],
  };
}

export default function FinancialAidDashboard() {
  return <CrownDashboardTemplate config={getFinancialAidDashboardConfig()} roleKey="financialAid" />;
}
