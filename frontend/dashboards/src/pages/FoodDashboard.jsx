import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function FoodDashboard() {
  const config = getDashboardTemplate('food');
  return <CrownDashboardTemplate config={config} roleKey="food" />;
}
