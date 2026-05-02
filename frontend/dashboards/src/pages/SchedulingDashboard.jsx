import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function SchedulingDashboard() {
  const config = getDashboardTemplate('scheduling');
  return <CrownDashboardTemplate config={config} roleKey="scheduling" />;
}
