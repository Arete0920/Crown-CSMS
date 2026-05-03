import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function GradebookDashboard() {
  const config = getDashboardTemplate('gradebook');
  return <CrownDashboardTemplate config={config} roleKey="gradebook" />;
}
