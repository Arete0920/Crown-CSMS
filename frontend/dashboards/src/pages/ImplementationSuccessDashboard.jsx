import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ImplementationSuccessDashboard() {
  const config = getDashboardTemplate('implementationSuccess');
  return <CrownDashboardTemplate config={config} roleKey="implementationSuccess" />;
}
