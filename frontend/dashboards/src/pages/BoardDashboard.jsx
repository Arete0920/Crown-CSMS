import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function BoardDashboard() {
  const config = getDashboardTemplate('board');
  return <CrownDashboardTemplate config={config} roleKey="board" />;
}
