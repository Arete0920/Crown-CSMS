import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function PortraitServiceHoursDashboard() {
  const config = getDashboardTemplate('portraitService');
  return <CrownDashboardTemplate config={config} roleKey="portraitService" />;
}
