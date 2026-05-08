import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function MarketingDashboard() {
  const config = getDashboardTemplate('marketing');
  return <CrownDashboardTemplate config={config} roleKey="marketing" />;
}
