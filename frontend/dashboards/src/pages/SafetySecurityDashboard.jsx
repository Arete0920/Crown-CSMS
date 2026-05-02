import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function SafetySecurityDashboard() {
  const config = getDashboardTemplate('safetySecurity');
  return <CrownDashboardTemplate config={config} roleKey="safetySecurity" />;
}
