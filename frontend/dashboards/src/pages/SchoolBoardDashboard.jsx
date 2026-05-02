import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function SchoolBoardDashboard() {
  const config = getDashboardTemplate('schoolBoard');
  return <CrownDashboardTemplate config={config} roleKey="schoolBoard" />;
}
