import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function AttendanceDashboard() {
  const config = getDashboardTemplate('attendance');
  return <CrownDashboardTemplate config={config} roleKey="attendance" />;
}
