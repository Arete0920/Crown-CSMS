import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ExtendedCareDashboard() {
  const config = getDashboardTemplate('extendedCare');
  return <CrownDashboardTemplate config={config} roleKey="extendedCare" />;
}
