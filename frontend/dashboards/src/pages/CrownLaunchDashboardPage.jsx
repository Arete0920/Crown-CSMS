import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const CROWN_LAUNCH_KPI = [
  { label: 'Enrolled', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Rate', value: '—', dataSource: 'SIS' },
  { label: 'Open Incidents', value: '—', dataSource: 'SIS' },
  { label: 'Pending Actions', value: '—', dataSource: 'SIS' }
];

export default function CrownLaunchDashboardPage({ activePath = '/admin' }) {
  const config = {
    ...getDashboardTemplate('schoolAdministrator'),
    activePath,
    kpiStrip: CROWN_LAUNCH_KPI,
  };

  return <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />;
}
