import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function DashboardCertificationCenter() {
  const config = getDashboardTemplate('dashboardCertificationCenter');
  return <CrownDashboardTemplate config={config} roleKey="dashboardCertificationCenter" />;
}
