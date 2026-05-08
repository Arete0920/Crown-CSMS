import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function AdmissionsDashboard() {
  const config = getDashboardTemplate('admissions');
  return <CrownDashboardTemplate config={config} roleKey="admissions" />;
}
