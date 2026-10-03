import ClassroomOperations from '../features/classroomExperience/ClassroomOperations.jsx';
import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function TeacherDashboard() {
  const config = getDashboardTemplate('teacher');
  return <><CrownDashboardTemplate config={config} roleKey="teacher" /><details><summary>Open classroom operations and records</summary><ClassroomOperations audience="teacher" /><ClassroomWorkspace audience="teacher" /></details></>;
}
