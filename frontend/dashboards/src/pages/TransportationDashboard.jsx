import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function TransportationDashboard() {
  const config = getDashboardTemplate('transportation');
  return <CrownDashboardTemplate config={config} roleKey="transportation" />;
}
