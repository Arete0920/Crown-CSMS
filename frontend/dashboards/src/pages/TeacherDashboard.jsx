import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function TeacherDashboard() {
  const config = getDashboardTemplate('teacher');
  return <><ClassroomWorkspace audience="teacher" /><CrownDashboardTemplate config={config} roleKey="teacher" /></>;
}
