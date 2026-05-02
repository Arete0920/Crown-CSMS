import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function VolunteerManagementDashboard() {
  const config = getDashboardTemplate('volunteerManagement');
  return <CrownDashboardTemplate config={config} roleKey="volunteerManagement" />;
}
