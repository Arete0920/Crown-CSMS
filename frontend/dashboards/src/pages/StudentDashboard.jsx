import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const STUDENT_KPI = [
  { label: 'GPA', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Rate', value: '—', dataSource: 'SIS' },
  { label: 'Assignments Due', value: '—', dataSource: 'SIS' },
  { label: 'Upcoming Events', value: '—', dataSource: 'SIS' }
];

export default function StudentDashboard() {
  const config = { ...getDashboardTemplate('student'), kpiStrip: STUDENT_KPI };
  return <CrownDashboardTemplate config={config} roleKey="student" />;
}
