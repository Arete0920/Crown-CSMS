import { Navigate } from 'react-router';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxFinanceTransactionPanel from '../components/finance/SandboxFinanceTransactionPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import { getCurrentUserRoles } from '../auth/roleAdapter';
import { hasAnyRole } from '../auth/roleAccess';

const ADMISSIONS_ALLOWED_ROLES = [
  'super_admin',
  'school_admin',
  'head_of_school',
  'admissions_manager',
  'admissions_director',
  'admin',
  'director',
  'principal',
];

export default function CrownLaunchModulePage({ moduleKey = 'admissions', activePath = '/admissions' }) {
  if (moduleKey === 'admissions' && !hasAnyRole(getCurrentUserRoles(), ADMISSIONS_ALLOWED_ROLES)) {
    return <Navigate to="/not-authorized" replace />;
  }

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
