import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ChaplainSpiritualLifeDashboard() {
  const config = getDashboardTemplate('chaplainSpiritualLife');
  return <CrownDashboardTemplate config={config} roleKey="chaplainSpiritualLife" />;
}
