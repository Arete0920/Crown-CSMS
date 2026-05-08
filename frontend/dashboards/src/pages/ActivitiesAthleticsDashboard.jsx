import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ActivitiesAthleticsDashboard() {
  const config = getDashboardTemplate('activitiesAthletics');
  return <CrownDashboardTemplate config={config} roleKey="activitiesAthletics" />;
}
