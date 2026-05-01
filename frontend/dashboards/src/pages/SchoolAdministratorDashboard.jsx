import AdminCommandCenterClean from './AdminCommandCenterClean.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const SCHOOL_ADMIN_KPI = [
  { label: 'Enrolled', value: '—', dataSource: 'SIS' },
  { label: 'Attendance Rate', value: '—', dataSource: 'SIS' },
  { label: 'Faculty & Staff', value: '—', dataSource: 'HRIS' },
  { label: 'Open Incidents', value: '—', dataSource: 'SIS' }
];

export default function SchoolAdministratorDashboard() {  return (
    <>
      <KpiStrip cards={SCHOOL_ADMIN_KPI} />
      <AdminCommandCenterClean />
    </>
  );
}
