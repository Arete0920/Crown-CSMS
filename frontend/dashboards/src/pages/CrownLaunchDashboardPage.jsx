import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function CrownLaunchDashboardPage({ activePath = '/admin' }) {
  const config = {
    ...getDashboardTemplate('schoolAdministrator'),
    activePath,
  };

  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
}