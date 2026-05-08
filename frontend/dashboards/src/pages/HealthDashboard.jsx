import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function HealthDashboard() {
  const config = getDashboardTemplate('health');
  return <CrownDashboardTemplate config={config} roleKey="health" />;
}
