import StudentHealth from '../features/studentHealth/StudentHealth.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function HealthOfficeDashboard() {
  const config = getDashboardTemplate('healthOffice');
  return <><CrownDashboardTemplate config={config} roleKey="healthOffice" /><StudentHealth /></>;
}
