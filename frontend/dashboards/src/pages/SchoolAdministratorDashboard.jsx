import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function SchoolAdministratorDashboard() {
  const config = getDashboardTemplate('schoolAdministrator');
  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
}
