import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxStudentSelfService from '../components/student/SandboxStudentSelfService.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function StudentDashboard() {
  const config = getDashboardTemplate('student');
  return (
    <>
      <CrownDashboardTemplate config={config} roleKey="student" />
      <SandboxStudentSelfService />
      <details><summary>Open my classroom work and feedback</summary><ClassroomWorkspace audience="student" /></details>
    </>
  );
}
