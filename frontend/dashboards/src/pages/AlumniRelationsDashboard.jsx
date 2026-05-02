import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function AlumniRelationsDashboard() {
  const config = getDashboardTemplate('alumniRelations');
  return <CrownDashboardTemplate config={config} roleKey="alumniRelations" />;
}
