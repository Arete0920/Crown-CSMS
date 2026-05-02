import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function AthleticsDirectorDashboard() {
  const config = getDashboardTemplate('athleticsDirector');
  return <CrownDashboardTemplate config={config} roleKey="athleticsDirector" />;
}
