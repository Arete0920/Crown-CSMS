import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function HRDashboard() {
  const config = getDashboardTemplate('hr');
  return <CrownDashboardTemplate config={config} roleKey="hr" />;
}
