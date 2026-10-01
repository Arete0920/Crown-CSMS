import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxStudentSelfService from '../components/student/SandboxStudentSelfService.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function StudentDashboard() {
  const config = getDashboardTemplate('student');
  return (
    <>
      <ClassroomWorkspace audience="student" />
      <SandboxStudentSelfService />
      <CrownDashboardTemplate config={config} roleKey="student" />
    </>
  );
}
