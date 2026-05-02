import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function CurriculumPDDashboard() {
  const config = getDashboardTemplate('curriculumPD');
  return <CrownDashboardTemplate config={config} roleKey="curriculumPD" />;
}
