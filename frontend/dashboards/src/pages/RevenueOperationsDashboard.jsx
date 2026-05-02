import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function RevenueOperationsDashboard() {
  const config = getDashboardTemplate('revenueOperations');
  return <CrownDashboardTemplate config={config} roleKey="revenueOperations" />;
}
