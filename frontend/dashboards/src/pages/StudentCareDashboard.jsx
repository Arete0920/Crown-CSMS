import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function StudentCareDashboard() {
  const config = getDashboardTemplate('studentCare');
  return <CrownDashboardTemplate config={config} roleKey="studentCare" />;
}
