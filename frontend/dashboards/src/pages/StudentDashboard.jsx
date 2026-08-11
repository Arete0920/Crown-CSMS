import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxStudentSelfService from '../components/student/SandboxStudentSelfService.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function StudentDashboard() {
  const config = getDashboardTemplate('student');
  return (
    <>
      <SandboxStudentSelfService />
      <CrownDashboardTemplate config={config} roleKey="student" />
    </>
  );
}
