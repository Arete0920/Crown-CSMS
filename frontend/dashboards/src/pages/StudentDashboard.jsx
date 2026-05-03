import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function StudentDashboard() {
  const config = getDashboardTemplate('student');
  return <CrownDashboardTemplate config={config} roleKey="student" />;
}
