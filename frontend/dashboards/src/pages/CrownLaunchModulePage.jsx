import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxFinanceTransactionPanel from '../components/finance/SandboxFinanceTransactionPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function CrownLaunchModulePage({ moduleKey = 'admissions', activePath = '/admissions' }) {
  const config = {
    ...getDashboardTemplate(moduleKey),
    activePath,
  };

  return (
    <>
      {moduleKey === 'finance' ? <SandboxFinanceTransactionPanel /> : null}
      <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />
    </>
  );
}
