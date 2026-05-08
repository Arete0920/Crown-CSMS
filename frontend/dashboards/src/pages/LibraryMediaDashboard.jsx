import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function LibraryMediaDashboard() {
  const config = getDashboardTemplate('libraryMedia');
  return <CrownDashboardTemplate config={config} roleKey="libraryMedia" />;
}
