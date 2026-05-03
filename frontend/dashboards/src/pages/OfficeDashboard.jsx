import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function OfficeDashboard() {
  const config = getDashboardTemplate('office');
  return <CrownDashboardTemplate config={config} roleKey="office" />;
}
