import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function ITDashboard() {
  const config = getDashboardTemplate('it');
  return <CrownDashboardTemplate config={config} roleKey="it" />;
}
