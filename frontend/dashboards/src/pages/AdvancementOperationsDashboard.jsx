import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function AdvancementOperationsDashboard() {
  const config = getDashboardTemplate('advancementOperations');
  return <CrownDashboardTemplate config={config} roleKey="advancementOperations" />;
}
