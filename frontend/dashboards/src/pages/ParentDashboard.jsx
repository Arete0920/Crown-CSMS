import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function ParentDashboard() {
  const config = getDashboardTemplate('parent');
  return <CrownDashboardTemplate config={config} roleKey="parent" />;
}
