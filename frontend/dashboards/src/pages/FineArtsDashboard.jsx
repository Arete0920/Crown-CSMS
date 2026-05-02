import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function FineArtsDashboard() {
  const config = getDashboardTemplate('fineArts');
  return <CrownDashboardTemplate config={config} roleKey="fineArts" />;
}
