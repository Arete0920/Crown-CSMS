import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function CommunicationsDashboard() {
  const config = getDashboardTemplate('communications');
  return <CrownDashboardTemplate config={config} roleKey="communications" />;
}
