import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function NetworkBenchmarkingDashboard() {
  const config = getDashboardTemplate('networkBenchmarking');
  return <CrownDashboardTemplate config={config} roleKey="networkBenchmarking" />;
}
