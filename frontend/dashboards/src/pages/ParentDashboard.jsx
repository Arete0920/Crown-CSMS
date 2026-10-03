import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import ParentSandboxDailyPanel from '../features/parentJourney/ParentSandboxDailyPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function ParentDashboard() {
  const config = getDashboardTemplate('parent');
  return (
    <>
      <CrownDashboardTemplate config={config} roleKey="parent" />
      <ParentSandboxDailyPanel />
      <details><summary>Open my children's classroom records</summary><ClassroomWorkspace audience="parent" /></details>
    </>
  );
}
