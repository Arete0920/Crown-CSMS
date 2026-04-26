import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function CrownLaunchModulePage({ moduleKey = 'admissions', activePath = '/admissions' }) {
  const config = {
    ...getDashboardTemplate(moduleKey),
    activePath,
  };

  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
}