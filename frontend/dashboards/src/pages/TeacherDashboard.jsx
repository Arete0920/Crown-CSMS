import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function TeacherDashboard() {
  const config = getDashboardTemplate('teacher');
  return <CrownDashboardTemplate config={config} roleKey="teacher" />;
}
