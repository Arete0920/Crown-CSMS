import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

/*
  CROWN - Financial Aid Dashboard
  - Gold template: CrownDashboardTemplate
  - Config key: financialAid
*/

export default function FinancialAidDashboard() {
  const config = getDashboardTemplate('financialAid');
  return <CrownDashboardTemplate config={config} roleKey="financialAid" />;
}
