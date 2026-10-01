import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function BoardDashboard() {
  const config = getDashboardTemplate('board');
  return <><ClassroomWorkspace audience="board" /><CrownDashboardTemplate config={config} roleKey="board" /></>;
}
