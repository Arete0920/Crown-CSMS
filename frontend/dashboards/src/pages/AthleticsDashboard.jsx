import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function AthleticsDashboard() {
  const config = getDashboardTemplate('athletics');
  return <CrownDashboardTemplate config={config} roleKey="athletics" />;
}
