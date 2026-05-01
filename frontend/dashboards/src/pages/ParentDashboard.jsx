import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const PARENT_KPI = [
  { label: 'Child GPA', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Rate', value: '—', dataSource: 'SIS' },
  { label: 'Upcoming Events', value: '—', dataSource: 'SIS' },
  { label: 'Messages', value: '—', dataSource: 'Comms' }
];

export default function ParentDashboard() {
  const config = { ...getDashboardTemplate('parent'), kpiStrip: PARENT_KPI };
  return <CrownDashboardTemplate config={config} roleKey="parent" />;
}
