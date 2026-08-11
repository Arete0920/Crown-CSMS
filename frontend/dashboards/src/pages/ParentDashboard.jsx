import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import ParentSandboxDailyPanel from '../features/parentJourney/ParentSandboxDailyPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function ParentDashboard() {
  const config = getDashboardTemplate('parent');
  return (
    <>
      <ParentSandboxDailyPanel />
      <CrownDashboardTemplate config={config} roleKey="parent" />
    </>
  );
}
