import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function SpiritualLifeDashboard() {
  const config = getDashboardTemplate('spiritualLife');
  return <CrownDashboardTemplate config={config} roleKey="spiritualLife" />;
}
