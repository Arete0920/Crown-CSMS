import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function ReleaseReliabilityDashboard() {
  const config = getDashboardTemplate('releaseReliability');
  return <CrownDashboardTemplate config={config} roleKey="releaseReliability" />;
}
