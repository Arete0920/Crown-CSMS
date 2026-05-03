import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ITSupportDashboard() {
  const config = getDashboardTemplate('itSupport');
  return <CrownDashboardTemplate config={config} roleKey="itSupport" />;
}
