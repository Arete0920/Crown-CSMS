import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function FacilitiesDashboard() {
  const config = getDashboardTemplate('facilities');
  return <CrownDashboardTemplate config={config} roleKey="facilities" />;
}
