import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

const TEACHER_KPI = [
  { label: 'My Classes', value: '—', dataSource: 'SIS' },
  { label: 'Students Rostered', value: '—', dataSource: 'SIS' },
  { label: 'Assignments Due', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Rate', value: '—', dataSource: 'SIS' }
];

export default function TeacherDashboard() {
  const config = { ...getDashboardTemplate('teacher'), kpiStrip: TEACHER_KPI };
  return <CrownDashboardTemplate config={config} roleKey="teacher" />;
}
