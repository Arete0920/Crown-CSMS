import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function RegistrarDashboard() {
  const config = getDashboardTemplate('registrar');
  return <CrownDashboardTemplate config={config} roleKey="registrar" />;
}
