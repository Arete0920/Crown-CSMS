import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import StaffRequirements from '../features/staffRequirements/StaffRequirements.jsx';
export default function HRDashboard() {
  const config = getDashboardTemplate('hr');
  return <><CrownDashboardTemplate config={config} roleKey="hr" /><StaffRequirements /></>;
}
