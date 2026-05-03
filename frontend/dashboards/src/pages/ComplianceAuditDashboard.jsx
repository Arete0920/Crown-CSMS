import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
export default function ComplianceAuditDashboard() {
  const config = getDashboardTemplate('complianceAudit');
  return <CrownDashboardTemplate config={config} roleKey="complianceAudit" />;
}
