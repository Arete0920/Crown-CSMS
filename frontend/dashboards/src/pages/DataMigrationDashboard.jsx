import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function DataMigrationDashboard() {
  const config = getDashboardTemplate('dataMigration');
  return <CrownDashboardTemplate config={config} roleKey="dataMigration" />;
}
