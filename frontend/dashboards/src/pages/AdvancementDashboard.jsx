import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function AdvancementDashboard() {
  const config = getDashboardTemplate('advancement');
  return <CrownDashboardTemplate config={config} roleKey="advancement" />;
}
