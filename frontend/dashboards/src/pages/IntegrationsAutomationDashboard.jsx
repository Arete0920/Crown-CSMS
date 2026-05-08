import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function IntegrationsAutomationDashboard() {
  const config = getDashboardTemplate('integrationsAutomation');
  return <CrownDashboardTemplate config={config} roleKey="integrationsAutomation" />;
}
